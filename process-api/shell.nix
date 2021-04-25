{ pkgs ? import ../nix { nixpkgs = sources."nixpkgs-20.09"; }
, sources ? import ../nix/sources.nix {}
, python ? "python39"
, setup ? import ./setup.nix { inherit pkgs python; }
}:

pkgs.mkShell {
  buildInputs = with pkgs; [
    cachix
    jfrog-cli
    jq
    pip2nix-20_09.python39
    setup.env
    vault
  ];
}

