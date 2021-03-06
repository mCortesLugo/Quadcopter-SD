# typed: false
# frozen_string_literal: true

describe Cask::Cmd::Zap, :cask do
  it "shows an error when a bad Cask is provided" do
    expect { described_class.run("notacask") }
      .to raise_error(Cask::CaskUnavailableError, /is unavailable/)
  end

  it "can zap and unlink multiple Casks at once" do
    caffeine = Cask::CaskLoader.load(cask_path("local-caffeine"))
    transmission = Cask::CaskLoader.load(cask_path("local-transmission"))

    Cask::Installer.new(caffeine).install
    Cask::Installer.new(transmission).install

    expect(caffeine).to be_installed
    expect(transmission).to be_installed

    described_class.run("local-caffeine", "local-transmission")

    expect(caffeine).not_to be_installed
    expect(caffeine.config.appdir.join("Caffeine.app")).not_to be_a_symlink
    expect(transmission).not_to be_installed
    expect(transmission.config.appdir.join("Transmission.app")).not_to be_a_symlink
  end
end
