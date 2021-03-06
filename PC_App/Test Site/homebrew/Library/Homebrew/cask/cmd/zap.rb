# typed: false
# frozen_string_literal: true

module Cask
  class Cmd
    # Cask implementation for the `brew uninstall` command.
    #
    # @api private
    class Zap < AbstractCommand
      extend T::Sig

      def self.parser
        super do
          switch "--force",
                 description: "Ignore errors when removing files."
        end
      end

      sig { void }
      def run
        self.class.zap_casks(*casks, verbose: args.verbose?, force: args.force?)
      end

      sig { params(casks: Cask, force: T.nilable(T::Boolean), verbose: T.nilable(T::Boolean)).void }
      def self.zap_casks(
        *casks,
        force: nil,
        verbose: nil
      )
        require "cask/installer"

        casks.each do |cask|
          odebug "Zapping Cask #{cask}"

          if cask.installed?
            if (installed_caskfile = cask.installed_caskfile) && installed_caskfile.exist?
              # Use the same cask file that was used for installation, if possible.
              cask = CaskLoader.load(installed_caskfile)
            end
          else
            raise CaskNotInstalledError, cask unless force
          end

          Installer.new(cask, verbose: verbose, force: force).zap
        end
      end
    end
  end
end
