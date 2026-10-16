# Import provenance

Agent definitions, setup tooling, factory research and the complete five-file `follow-the-rules` skill were imported from [killallgit/killall-skills at a016d77ff5f86821f0292a5a00dbf4600b0d8a15](https://github.com/killallgit/killall-skills/tree/a016d77ff5f86821f0292a5a00dbf4600b0d8a15). The rules skill remains in both repositories by explicit choice; there is no automatic synchronization.

The setup eval helper now uses checked-in historical runtime snapshots. Each snapshot records its original repository and full commit; runtime file contents are unchanged from those commits.

The old Go prototype was removed from the working tree without rewriting repository history.
