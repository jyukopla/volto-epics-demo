{ nixpkgs ? sources.nixpkgs
, config ? {}
, sources ? import ./sources.nix
}:

let

  overlay = _: pkgs: {

    gitignoreSource = (import sources.gitignore {
      inherit (pkgs) lib;
    }).gitignoreSource;

    mvn2nix = (import sources.mvn2nix {
      inherit nixpkgs;
    }).mvn2nix;

    # pip2nix branches require specific nixpkgs branch (for pip)
    pip2nix = ((import (sources."pip2nix-20.03" + "/release.nix") {
      pkgs = import sources."nixpkgs-20.03" {};
    }).pip2nix);

    # pip2nix branches require specific nixpkgs branch (for pip)
    pip2nix-20_09 = ((import (sources."pip2nix-20.09" + "/release.nix") {
      pkgs = import sources."nixpkgs-20.09" {};
    }).pip2nix);

    # node2nix with nodejs 14 support
    node2nix = builtins.getAttr builtins.currentSystem(
      import (sources.node2nix + "/release.nix") {
        nixpkgs = sources."nixpkgs-20.09";
        systems = [ builtins.currentSystem ];
    }).package;

    levant = pkgs.buildGoPackage rec {
      name = "levant-${version}";
      version = "2020-11-06";
      src = sources.levant;
      goPackagePath = "github.com/hashicorp/levant";
      goDeps = ./levant-deps.nix;
      preBuild = ''
        rm -r go/src/github.com/hashicorp/nomad/vendor/github.com/hashicorp/nomad
      '';
    };

    # artifactory deployment
    jfrog-cli = pkgs.buildGoPackage rec {
      name = "jfrog-cli-${version}";
      version = "1.39.1";
      goPackagePath = "github.com/jfrog/jfrog-cli";
      src = sources.jfrog-cli;
      goDeps = ./jfrog-cli-1.39.1-deps.nix;
      postPatch = "rm -r testdata";
    };
  };

  pkgs = import nixpkgs {
    overlays = [ overlay ];
    inherit config;
  };

in pkgs
