# frozen_string_literal: true

require 'ruby-progressbar/output'
require 'ruby-progressbar/outputs/tty'
require 'ruby-progressbar/outputs/non_tty'
require 'ruby-progressbar/timer'
require 'ruby-progressbar/progress'
require 'ruby-progressbar/throttle'
require 'ruby-progressbar/calculators/length'
require 'ruby-progressbar/calculators/running_average'
require 'ruby-progressbar/components'
require 'ruby-progressbar/format'
require 'ruby-progressbar/base'
require 'ruby-progressbar/refinements' if Module.
                                         private_instance_methods.
                                         include?(:using)

class ProgressBar
  def self.create(*args)
    ProgressBar::Base.new(*args)
  end
end
