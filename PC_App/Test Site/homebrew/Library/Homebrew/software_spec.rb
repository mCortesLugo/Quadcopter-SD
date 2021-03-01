# typed: false
# frozen_string_literal: true

require "resource"
require "download_strategy"
require "checksum"
require "version"
require "options"
require "build_options"
require "dependency_collector"
require "utils/bottles"
require "patch"
require "compilers"
require "global"
require "os/mac/version"
require "extend/on_os"

class SoftwareSpec
  extend T::Sig

  extend Forwardable
  include OnOS

  PREDEFINED_OPTIONS = {
    universal: Option.new("universal", "Build a universal binary"),
    cxx11:     Option.new("c++11",     "Build using C++11 mode"),
  }.freeze

  attr_reader :name, :full_name, :owner, :build, :resources, :patches, :options, :deprecated_flags,
              :deprecated_options, :dependency_collector, :bottle_specification, :compiler_failures,
              :uses_from_macos_elements, :bottle_disable_reason

  def_delegators :@resource, :stage, :fetch, :verify_download_integrity, :source_modified_time, :download_name,
                 :cached_download, :clear_cache, :checksum, :mirrors, :specs, :using, :version, :mirror,
                 :downloader

  def_delegators :@resource, :sha256

  def initialize(flags: [])
    @resource = Resource.new
    @resources = {}
    @dependency_collector = DependencyCollector.new
    @bottle_specification = BottleSpecification.new
    @patches = []
    @options = Options.new
    @flags = flags
    @deprecated_flags = []
    @deprecated_options = []
    @build = BuildOptions.new(Options.create(@flags), options)
    @compiler_failures = []
    @bottle_disable_reason = nil
  end

  def owner=(owner)
    @name = owner.name
    @full_name = owner.full_name
    @bottle_specification.tap = owner.tap
    @owner = owner
    @resource.owner = self
    resources.each_value do |r|
      r.owner = self
      r.version ||= begin
        raise "#{full_name}: version missing for \"#{r.name}\" resource!" if version.nil?

        if version.head?
          Version.create("HEAD")
        else
          version.dup
        end
      end
    end
    patches.each { |p| p.owner = self }
  end

  def url(val = nil, specs = {})
    return @resource.url if val.nil?

    @resource.url(val, specs)
    dependency_collector.add(@resource)
  end

  def bottle_unneeded?
    return false unless @bottle_disable_reason

    @bottle_disable_reason.unneeded?
  end

  sig { returns(T::Boolean) }
  def bottle_disabled?
    @bottle_disable_reason ? true : false
  end

  def bottle_defined?
    !bottle_specification.collector.keys.empty?
  end

  def bottle_tag?
    bottle_specification.tag?(Utils::Bottles.tag)
  end

  def bottled?
    bottle_tag? && \
      (bottle_specification.compatible_locations? || owner.force_bottle)
  end

  def bottle(disable_type = nil, disable_reason = nil, &block)
    if disable_type
      @bottle_disable_reason = BottleDisableReason.new(disable_type, disable_reason)
    else
      bottle_specification.instance_eval(&block)
    end
  end

  def resource_defined?(name)
    resources.key?(name)
  end

  def resource(name, klass = Resource, &block)
    if block
      raise DuplicateResourceError, name if resource_defined?(name)

      res = klass.new(name, &block)
      return unless res.url

      resources[name] = res
      dependency_collector.add(res)
    else
      resources.fetch(name) { raise ResourceMissingError.new(owner, name) }
    end
  end

  def go_resource(name, &block)
    resource name, Resource::Go, &block
  end

  def option_defined?(name)
    options.include?(name)
  end

  def option(name, description = "")
    opt = PREDEFINED_OPTIONS.fetch(name) do
      unless name.is_a?(String)
        raise ArgumentError, "option name must be string or symbol; got a #{name.class}: #{name}"
      end
      raise ArgumentError, "option name is required" if name.empty?
      raise ArgumentError, "option name must be longer than one character: #{name}" unless name.length > 1
      raise ArgumentError, "option name must not start with dashes: #{name}" if name.start_with?("-")

      Option.new(name, description)
    end
    options << opt
  end

  def deprecated_option(hash)
    raise ArgumentError, "deprecated_option hash must not be empty" if hash.empty?

    hash.each do |old_options, new_options|
      Array(old_options).each do |old_option|
        Array(new_options).each do |new_option|
          deprecated_option = DeprecatedOption.new(old_option, new_option)
          deprecated_options << deprecated_option

          old_flag = deprecated_option.old_flag
          new_flag = deprecated_option.current_flag
          next unless @flags.include? old_flag

          @flags -= [old_flag]
          @flags |= [new_flag]
          @deprecated_flags << deprecated_option
        end
      end
    end
    @build = BuildOptions.new(Options.create(@flags), options)
  end

  def depends_on(spec)
    dep = dependency_collector.add(spec)
    add_dep_option(dep) if dep
  end

  def uses_from_macos(spec, _bounds = {})
    spec = spec.dup.shift if spec.is_a?(Hash)
    depends_on(spec)
  end

  def deps
    dependency_collector.deps
  end

  def recursive_dependencies
    deps_f = []
    recursive_dependencies = deps.map do |dep|
      deps_f << dep.to_formula
      dep
    rescue TapFormulaUnavailableError
      # Don't complain about missing cross-tap dependencies
      next
    end.compact.uniq
    deps_f.compact.each do |f|
      f.recursive_dependencies.each do |dep|
        recursive_dependencies << dep unless recursive_dependencies.include?(dep)
      end
    end
    recursive_dependencies
  end

  def requirements
    dependency_collector.requirements
  end

  def recursive_requirements
    Requirement.expand(self)
  end

  def patch(strip = :p1, src = nil, &block)
    p = Patch.create(strip, src, &block)
    dependency_collector.add(p.resource) if p.is_a? ExternalPatch
    patches << p
  end

  def fails_with(compiler, &block)
    compiler_failures << CompilerFailure.create(compiler, &block)
  end

  def needs(*standards)
    standards.each do |standard|
      compiler_failures.concat CompilerFailure.for_standard(standard)
    end
  end

  def add_dep_option(dep)
    dep.option_names.each do |name|
      if dep.optional? && !option_defined?("with-#{name}")
        options << Option.new("with-#{name}", "Build with #{name} support")
      elsif dep.recommended? && !option_defined?("without-#{name}")
        options << Option.new("without-#{name}", "Build without #{name} support")
      end
    end
  end
end

class HeadSoftwareSpec < SoftwareSpec
  def initialize(flags: [])
    super
    @resource.version = Version.create("HEAD")
  end

  def verify_download_integrity(_fn)
    # no-op
  end
end

class Bottle
  class Filename
    extend T::Sig

    attr_reader :name, :version, :tag, :rebuild

    def self.create(formula, tag, rebuild)
      new(formula.name, formula.pkg_version, tag, rebuild)
    end

    def initialize(name, version, tag, rebuild)
      @name = File.basename name
      @version = version
      @tag = tag.to_s
      @rebuild = rebuild
    end

    sig { returns(String) }
    def to_s
      "#{name}--#{version}#{extname}"
    end
    alias to_str to_s

    sig { returns(String) }
    def json
      "#{name}--#{version}.#{tag}.bottle.json"
    end

    def bintray
      ERB::Util.url_encode("#{name}-#{version}#{extname}")
    end

    sig { returns(String) }
    def extname
      s = rebuild.positive? ? ".#{rebuild}" : ""
      ".#{tag}.bottle#{s}.tar.gz"
    end
  end

  extend Forwardable

  attr_reader :name, :resource, :prefix, :cellar, :rebuild

  def_delegators :resource, :url, :verify_download_integrity
  def_delegators :resource, :cached_download, :clear_cache

  def initialize(formula, spec)
    @name = formula.name
    @resource = Resource.new
    @resource.owner = formula
    @resource.specs[:bottle] = true
    @spec = spec

    checksum, tag, cellar = spec.checksum_for(Utils::Bottles.tag)

    filename = Filename.create(formula, tag, spec.rebuild)
    @resource.url("#{spec.root_url}/#{filename.bintray}",
                  select_download_strategy(spec.root_url_specs))
    @resource.version = formula.pkg_version
    @resource.checksum = checksum
    @prefix = spec.prefix
    @cellar = cellar
    @rebuild = spec.rebuild
  end

  def fetch(verify_download_integrity: true)
    # add the default bottle domain as a fallback mirror
    if @resource.download_strategy == CurlDownloadStrategy &&
       @resource.url.start_with?(Homebrew::EnvConfig.bottle_domain)
      fallback_url = @resource.url
                              .sub(/^#{Regexp.escape(Homebrew::EnvConfig.bottle_domain)}/,
                                   HOMEBREW_BOTTLE_DEFAULT_DOMAIN)
      @resource.mirror(fallback_url) if [@resource.url, *@resource.mirrors].exclude?(fallback_url)
    end
    @resource.fetch(verify_download_integrity: verify_download_integrity)
  end

  def compatible_locations?
    @spec.compatible_locations?
  end

  # Does the bottle need to be relocated?
  def skip_relocation?
    @spec.skip_relocation?
  end

  def stage
    resource.downloader.stage
  end

  private

  def select_download_strategy(specs)
    specs[:using] ||= DownloadStrategyDetector.detect(@spec.root_url)
    specs
  end
end

class BottleSpecification
  extend T::Sig

  attr_rw :prefix, :rebuild
  attr_accessor :tap
  attr_reader :all_tags_cellar, :checksum, :collector, :root_url_specs, :repository

  sig { void }
  def initialize
    @rebuild = 0
    @prefix = Homebrew::DEFAULT_PREFIX
    @all_tags_cellar = Homebrew::DEFAULT_CELLAR
    @repository = Homebrew::DEFAULT_REPOSITORY
    @collector = Utils::Bottles::Collector.new
    @root_url_specs = {}
  end

  def prefix=(prefix)
    if [HOMEBREW_DEFAULT_PREFIX,
        HOMEBREW_MACOS_ARM_DEFAULT_PREFIX,
        HOMEBREW_LINUX_DEFAULT_PREFIX].exclude?(prefix)
      odisabled "setting 'prefix' for bottles"
    end
    @prefix = prefix
  end

  def root_url(var = nil, specs = {})
    if var.nil?
      @root_url ||= "#{Homebrew::EnvConfig.bottle_domain}/#{Utils::Bottles::Bintray.repository(tap)}"
    else
      @root_url = var
      @root_url_specs.merge!(specs)
    end
  end

  def cellar(val = nil)
    # TODO: (3.1) uncomment to deprecate the old bottle syntax
    # if val.present?
    #   odeprecated(
    #     "`cellar` in a bottle block",
    #     "`brew style --fix` on the formula to update the style or use `sha256` with a `cellar:` argument",
    #   )
    # end

    return collector.dig(Utils::Bottles.tag, :cellar) || @all_tags_cellar if val.nil?

    @all_tags_cellar = val
  end

  def compatible_locations?
    # this looks like it should check prefix and repository too but to be
    # `cellar :any` actually requires no references to the cellar, prefix or
    # repository.
    return true if [:any, :any_skip_relocation].include?(cellar)

    compatible_cellar = cellar == HOMEBREW_CELLAR.to_s
    compatible_prefix = prefix == HOMEBREW_PREFIX.to_s

    compatible_cellar && compatible_prefix
  end

  # Does the {Bottle} this {BottleSpecification} belongs to need to be relocated?
  sig { returns(T::Boolean) }
  def skip_relocation?
    cellar == :any_skip_relocation
  end

  sig { params(tag: Symbol, exact: T::Boolean).returns(T::Boolean) }
  def tag?(tag, exact: false)
    checksum_for(tag, exact: exact) ? true : false
  end

  # Checksum methods in the DSL's bottle block take
  # a Hash, which indicates the platform the checksum applies on.
  # Example bottle block syntax:
  # bottle do
  #  sha256 cellar: :any_skip_relocation, big_sur: "69489ae397e4645..."
  #  sha256 cellar: :any, catalina: "449de5ea35d0e94..."
  # end
  def sha256(hash)
    sha256_regex = /^[a-f0-9]{64}$/i

    # find new `sha256 big_sur: "69489ae397e4645..."` format
    tag, digest = hash.find do |key, value|
      key.is_a?(Symbol) && value.is_a?(String) && value.match?(sha256_regex)
    end

    if digest && tag
      # the cellar hash key only exists on the new format
      cellar = hash[:cellar]
    else
      # otherwise, find old `sha256 "69489ae397e4645..." => :big_sur` format
      digest, tag = hash.find do |key, value|
        key.is_a?(String) && value.is_a?(Symbol) && key.match?(sha256_regex)
      end

      # TODO: (3.1) uncomment to deprecate the old bottle syntax
      # if digest && tag
      #   odeprecated(
      #     '`sha256 "digest" => :tag` in a bottle block',
      #     '`brew style --fix` on the formula to update the style or use `sha256 tag: "digest"`',
      #   )
      # end
    end

    cellar ||= all_tags_cellar
    collector[tag] = { checksum: Checksum.new(digest), cellar: cellar }
  end

  sig { params(tag: Symbol, exact: T::Boolean).returns(T.nilable([Checksum, Symbol, T.any(Symbol, String)])) }
  def checksum_for(tag, exact: false)
    collector.fetch_checksum_for(tag, exact: exact)
  end

  def checksums
    tags = collector.keys.sort_by do |tag|
      version = OS::Mac::Version.from_symbol(tag)
      # Give arm64 bottles a higher priority so they are first
      priority = version.arch == :arm64 ? "2" : "1"
      "#{priority}.#{version}_#{tag}"
    rescue MacOSVersionError
      # Sort non-MacOS tags below MacOS tags.
      "0.#{tag}"
    end
    tags.reverse.map do |tag|
      {
        "tag"    => tag,
        "digest" => collector[tag][:checksum],
        "cellar" => collector[tag][:cellar],
      }
    end
  end
end

class PourBottleCheck
  include OnOS

  def initialize(formula)
    @formula = formula
  end

  def reason(reason)
    @formula.pour_bottle_check_unsatisfied_reason = reason
  end

  def satisfy(&block)
    @formula.send(:define_method, :pour_bottle?, &block)
  end
end

require "extend/os/software_spec"
