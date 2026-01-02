{
  pkgs,
  lib,
  config,
  ...
}:

{
  # ============================================================================
  # ENVIRONMENT CONFIGURATION
  # ============================================================================

  # https://devenv.sh/integrations/dotenv/
  dotenv = {
    enable = true;
    filename = [
      ".env"
      ".env.local"
    ];
  };

  # ============================================================================
  # LANGUAGE & RUNTIME
  # ============================================================================

  # https://devenv.sh/languages/
  # languages.go = {
  #   enable = true;
  #   package = pkgs.go;
  # };

  # ============================================================================
  # PACKAGES & TOOLS
  # ============================================================================

  # https://devenv.sh/packages/
  # https://search.nixos.org/packages
  packages =
    with pkgs;
    [
      pkgs.bash-completion # Enable bash programmable completion

      # Accounting
      # bean-check bean-doctor bean-example bean-format treeify
      pkgs.python313Packages.beancount
      pkgs.python313Packages.beancount-periodic
      pkgs.python313Packages.beangulp
      pkgs.python313Packages.beanquery
      pkgs.python313Packages.fava

      pkgs.python313Packages.regex
      pkgs.python313Packages.pytest

      # pdftotext
      pkgs.poppler-utils
    ]
    ++ lib.optionals pkgs.stdenv.isLinux [
      # Conditionally include glibcLocales only on Linux systems
      # to address potential locale warnings with tools like perl.
      # perl: warning: Setting locale failed.
      # perl: warning: Please check that your locale settings:
      pkgs.glibcLocales
    ];

  # ============================================================================
  # CLAUDE CODE CONFIGURATION
  # ============================================================================

  # imports = [
  #   ./nix/claude-code.nix
  # ];

  # ============================================================================
  # SCRIPTS
  # ============================================================================

  # https://devenv.sh/scripts/
  # enterShell = ''
  #   echo "Converting Nix MCP config to OpenCode JSON..."
  #   export DEVENV_ROOT="${config.devenv.root}"
  #   cd nix && make convert
  # '';

  # ============================================================================
  # GIT HOOKS CONFIGURATION
  # ============================================================================

  # https://devenv.sh/git-hooks/

  git-hooks.hooks = {

    # ==========================================================================
    # FAST VALIDATION (< 1s)
    # ==========================================================================

    # File format and integrity checks
    # check-xml = {
    #   enable = true;
    # };
    check-yaml = {
      enable = true;
    };
    check-json = {
      enable = true;
    };
    check-merge-conflicts = {
      enable = true;
    };
    check-case-conflicts = {
      enable = true;
    };
    check-executables-have-shebangs = {
      enable = true;
    };
    check-shebang-scripts-are-executable = {
      enable = true;
    };
    check-symlinks = {
      enable = true;
    };

    check-added-large-files = {
      enable = true;
      args = [ "--maxkb=1024" ]; # 1MB limit for API projects
    };

    # File formatting fixes
    end-of-file-fixer = {
      enable = true;
      excludes = [
        ".kilocode/"
        ".opencode/"
        ".specify/"
      ];
    };
    fix-byte-order-marker = {
      enable = true;
    };
    mixed-line-endings = {
      enable = true;
    };
    trim-trailing-whitespace = {
      enable = true;
      excludes = [
        ".kilocode/"
        ".opencode/"
        ".specify/"
      ];
    };

    # ==========================================================================
    # CODE FORMATTING (1-5s)
    # ==========================================================================

    # NIX
    nixfmt-rfc-style = {
      enable = true;
    };

    # GOLANG
    # Standard Go formatting
    # gofmt = {
    #   enable = true;
    # };

    # Go testing (requires serial execution)
    # gotest = {
    #   enable = true;
    # };

    # Go static analysis (requires serial execution)
    # govet = {
    #   enable = true;
    # };

    # Advanced static analysis for Go
    staticcheck = {
      enable = true;
      excludes = [ ".specify/" ];
    };

    # SHELL/BASH
    # shellcheck: Static analysis for shell scripts
    # shfmt: Shell script formatter (Google Bash Style Guide)
    shellcheck = {
      enable = true;
      excludes = [
        "^\\.envrc$"
        ".specify/"
      ]; # Exclude direnv config files and .specify directory
    };
    shfmt = {
      enable = true;
      entry = "${pkgs.shfmt}/bin/shfmt -i 2 -ci -bn -sr -w";
      types = [ "shell" ];
      pass_filenames = true;
      excludes = [
        ".kilocode/"
        ".opencode/"
        ".specify/"
      ];
    };

    # Custom bash variable syntax enforcement
    # bash-variable-braces = {
    #   enable = true;
    #   entry = "\\$[A-Za-z_][A-Za-z0-9_]*(?![}\\[])";
    #   language = "pygrep";
    #   files = "\\.(sh|bash)$";
    #   name = "Require \${VAR} instead of $VAR in bash scripts";
    #   description = "Require \${VAR} syntax instead of $VAR for bash variables";
    # };

    # YAML
    # MARKUP/CONFIG LANGUAGES
    yamllint = {
      enable = true;
    };

    # PYTHON
    # Black code formatter
    # black = {
    #   enable = true;
    #   args = [
    #     "--line-length"
    #     # "88"
    #     # "96"
    #     "100"
    #   ];
    # };

    # Ruff linter
    ruff = {
      enable = true;
    };

    # Ruff formatter
    ruff-format = {
      enable = true;
    };

    # isort import sorter
    # isort = {
    #   enable = true;
    #   args = [
    #     "--profile"
    #     "black"
    #   ];
    # };

    # Python syntax validation
    check-python = {
      enable = true;
    };

    # Debug statement detection
    python-debug-statements = {
      enable = true;
    };

    # ==========================================================================
    # BEANCOUNT VALIDATION AND FORMATTING
    # ==========================================================================

    # Check beancount files for syntax errors and validation
    bean-check-main = {
      enable = true;
      name = "bean-check-main";
      description = "Validate beancount ledger files";
      entry = "${pkgs.beancount}/bin/bean-check";
      files = "^ledger/main\\.bean$";
      types = [ "text" ];
    };

    bean-check-combined = {
      enable = true;
      name = "bean-check-combined";
      description = "Validate beancount ledger files";
      entry = "${pkgs.beancount}/bin/bean-check";
      files = "combined\\.bean$";
      types = [ "text" ];
    };

    bean-check-all = {
      enable = false;
      name = "bean-check-all";
      description = "Validate beancount ledger files";

      entry =
        let
          script = pkgs.writeShellScript "precommit-bean-check" ''
            set -e
            for file in "$@"; do
              ${pkgs.beancount}/bin/bean-check "$file"
            done
          '';
        in
        builtins.toString script;

      files = "\\.bean$";
      types = [ "text" ];
    };

    # Format beancount files
    bean-format = {
      enable = true;
      name = "bean-format";
      description = "Format beancount ledger files";
      entry = "${pkgs.beancount}/bin/bean-format --in-place";
      files = "\\.bean$";
      types = [ "text" ];
    };

    # ==========================================================================
    # SECURITY VALIDATION
    # ==========================================================================

    # Fast regex-based secret detection
    ripsecrets = {
      enable = true;
      excludes = [ "^\\.env$" ];
    };

    # SOPS encryption enforcement
    pre-commit-hook-ensure-sops = {
      enable = true;
    };

    # Comprehensive secrets scanner (slower but thorough)
    # trufflehog = {
    #   enable = true;
    #   pass_filenames = false;
    #   stages = [
    #     "pre-commit"
    #     "manual"
    #   ];
    # };

    # AWS credentials detection
    detect-aws-credentials = {
      enable = true;
      args = [ "--allow-missing-credentials" ];
    };

    # Private key detection
    detect-private-keys = {
      enable = true;
    };

    # VCS permalink validation
    check-vcs-permalinks = {
      enable = true;
    };

  };
}
