cask "version-latest" do
  version :latest
  sha256 :no_check

  url "file://#{TEST_FIXTURE_DIR}/cask/caffeines.zip"
  name "Version Latest"
  desc "Unversioned cask"
  homepage "https://brew.sh/"

  app "Caffeine Mini.app"
  app "Caffeine Pro.app"
end
