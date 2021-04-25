{ pkgs ? import ../nix { nixpkgs = sources."nixpkgs-20.09"; }
, sources ? import ../nix/sources.nix {}
, python ? "python39"
, setup ? import ./setup.nix { inherit pkgs python; }
}:

setup.build
