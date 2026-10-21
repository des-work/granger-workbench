# Third-party materials

The MIT license at the repository root applies to original project code. Bundled fonts and libraries keep their upstream licenses and notices, which are included under `assets-vault/licenses/` and with exported kits where applicable.

`assets-vault/dependencies.lock.json` records each vendored package's version, declared license, source tarball, integrity digest, retained files, and file SHA-256 hashes. See that inventory and the actual license texts when redistributing assets. `tools/vendor_design_assets.py` explicitly restores those pinned files from npm; routine asset lookups run locally.

Other Python and system dependencies are installed separately under their respective licenses. No model weights, speaker-enrollment profiles, voices, Kiwix ZIM archives, textbook libraries, or external Termstage/Sherlock projects are included. Users obtain those resources separately and are responsible for their applicable terms.
