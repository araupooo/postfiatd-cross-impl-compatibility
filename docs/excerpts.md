# Excerpts

Verbatim excerpts from both pinned commits, extracted by
`scripts/extract_excerpts.py`. Each file carries the postfiatd chunk
and the rippled 3.1.2 chunk (or a verified-absent note), headed with
repos, commits, files, lines, source SHA-256, git blob SHA, and size;
the table below records the excerpt digest from
`fixtures/source-hashes.json`.

| Excerpt | postfiatd file | Lines | rippled 3.1.2 reference | SHA-256 |
| --- | --- | --- | --- | --- |
| E01 | `src/xrpld/consensus/ConsensusParms.h` | 79-79 | rippled `src/xrpld/consensus/ConsensusParms.h` 79-79 | `36b1073c1218dd227ec928e456e7684004bd289484f3fa1abbc188fb553df6d1` |
| E02 | `src/xrpld/app/misc/detail/ValidatorList.cpp` | 1897-1900 | rippled `src/xrpld/app/misc/detail/ValidatorList.cpp` 1883-1886 | `ad5267518342a7184f082c9509be7bd31bdab3f103ba0cb9705c639a474cb351` |
| E03 | `include/xrpl/protocol/SystemParameters.h` | 83-87 | rippled `include/xrpl/protocol/SystemParameters.h` 83-87 | `28ebad12b379ab6a839e4d11d2ed5fb46869c2a64662bb1455243de483e55a50` |
| E04 | `src/xrpld/app/consensus/RCLConsensus.cpp` | 709-728 | rippled `src/xrpld/app/consensus/RCLConsensus.cpp` 704-728 | `d012cde477e79e13cc53fcee2e013b691480f9434f7a5b0fd0092eb47edb0401` |
| E05 | `src/xrpld/consensus/Consensus.h` | 1602-1613 | rippled `src/xrpld/consensus/Consensus.h` 1605-1616 | `caf740569d453a2a617e6e12204581ee8315befbc078ff6f23e5d0908daadb78` |
| E06 | `src/xrpld/consensus/Consensus.h` | 1283-1294 | rippled `src/xrpld/consensus/Consensus.h` 1283-1294 | `eec6699cdfd75f130ab2e102028bb8c41b9c54307a1cb82dfda6553f42680c74` |
| E07 | `src/xrpld/consensus/DisputedTx.h` | 117-132 | rippled `src/xrpld/consensus/DisputedTx.h` 117-132 | `cbb9e46d8b382f570ffb491313aa17957eeaf68bd8e04126974bb1684678901e` |
| E08 | `include/xrpl/protocol/STValidation.h` | 59-92 | rippled `include/xrpl/protocol/STValidation.h` 64-76 | `d6d87607dfe6aa0a709cad287699182c611f00068d5846fcf3bc645be93deb93` |
| E09 | `src/libxrpl/protocol/STValidation.cpp` | 123-150 | rippled `src/libxrpl/protocol/STValidation.cpp` 120-132 | `4226bef92cbecb79836054edbe8976052391e0ebeb1358854e1e26bce86d6ae8` |
| E10 | `src/libxrpl/protocol/STValidation.cpp` | 78-88 | rippled `src/libxrpl/protocol/STValidation.cpp` 75-82 | `ca6aa02fc8ae525536bec976c81a09b1ce2f7adaccccaf8af0ce9b34992a7bfc` |
| E11 | `src/xrpld/app/consensus/RCLValidations.cpp` | 193-226 | rippled `src/xrpld/app/consensus/RCLValidations.cpp` 193-199 | `e2cecff3a2cd35f4f1481767229bb4bb427faae49b59bab2e62eb922177f0bc4` |
| E12 | `src/xrpld/app/consensus/RCLConsensus.cpp` | 353-361 | absent in rippled (`ValidatorVoteTracker`: 0 hits in src/xrpld/app/consensus/RCLConsensus.cpp) | `3559e606fd686024b05e0f30a42cb94817bbe773f5fd82989fff3c189d186728` |
| E13 | `src/xrpld/app/misc/Manifest.h` | 246-290 | rippled `src/xrpld/app/misc/Manifest.h` 226-232 | `ad7ec2d08060a53a3d8ce3dc5a57f1de9c96360fd479c3e07699e660dde2095e` |
| E14 | `src/xrpld/app/misc/ValidatorList.h` | 570-585 | rippled `src/xrpld/app/misc/ValidatorList.h` 564-572 | `257a095f7267766f9f56ba565eac108a69c76599f33b9d4a20b1116de756de1f` |
| E15 | `src/xrpld/app/ledger/Ledger.cpp` | 180-205 | rippled `src/xrpld/app/ledger/Ledger.cpp` 180-186 | `f05c20dc9c5992474e553944bf1ee254a18c395f9b50990c78562fa523841b1a` |
| E16 | `include/xrpl/protocol/SystemParameters.h` | 35-38 | rippled `include/xrpl/protocol/SystemParameters.h` 35-38 | `e71f1c5b0d6b087e3db499f28ca82c39f9baf405a58b89a9cb51560b14fd8e04` |
| E17 | `include/xrpl/protocol/SystemParameters.h` | 70-76 | rippled `include/xrpl/protocol/SystemParameters.h` 70-76 | `6177a0b52fa21472507a977f0686dda6c2eebec22feacde36961245b745c4e97` |
| E18 | `src/xrpld/app/misc/SHAMapStoreImp.cpp` | 251-280 | rippled `src/xrpld/app/misc/SHAMapStoreImp.cpp` 248-258 | `5cf22a94ab42065e9ee597b6fe0843e3e6464904150548bb1bae71d2db2f2599` |
| E19 | `src/xrpld/app/misc/SHAMapStoreImp.cpp` | 371-392 | absent in rippled (`RotationExposureGuard`: 0 hits in src/xrpld/app/misc/SHAMapStoreImp.cpp) | `599121057925082fcd4529f1a38ad51fa3549fe17b03bed3fc93eaa0146d7bc6` |
| E20 | `src/xrpld/shamap/detail/SHAMapNodeID.cpp` | 57-75 | rippled `src/xrpld/shamap/detail/SHAMapNodeID.cpp` 57-66 | `a42986a3dcc1fc7694fa553f673f01102ddd622d8c7aa48a25db253ebef2a85f` |
| E21 | `src/xrpld/shamap/detail/SHAMapNodeID.cpp` | 128-160 | rippled `src/xrpld/shamap/detail/SHAMapNodeID.cpp` 128-152 | `081e4b7ba2f154c3c81b8fe61c48b9ef6c41b8298ff4a1dbbcaf08ac5d8c1f85` |
| E22 | `src/xrpld/app/ledger/detail/LedgerReplayMsgHandler.h` | 27-80 | rippled `src/xrpld/app/ledger/detail/LedgerReplayMsgHandler.h` 27-65 | `5d415cab1ccd477b912fdc00c59e5fe143fd3251c6a62d1c481ef00041a87848` |
| E23 | `src/xrpld/app/ledger/detail/LedgerReplayMsgHandler.cpp` | 105-130 | rippled `src/xrpld/app/ledger/detail/LedgerReplayMsgHandler.cpp` 103-120 | `11d9b231b6bac9d74e6420afcf3d7c96427675f76d4db4109b1303b0af78036f` |
| E24 | `src/xrpld/app/ledger/detail/LedgerMaster.cpp` | 286-310 | absent in rippled (`ExclusionManager`: 0 hits in src/xrpld/app/ledger/detail/LedgerMaster.cpp) | `257939dac9b45249b9f33de4238475f6cfef75269c88ed4609ef98f64da818f6` |
| E25 | `src/xrpld/app/ledger/ConsensusTransSetSF.cpp` | 64-85 | rippled `src/xrpld/app/ledger/ConsensusTransSetSF.cpp` 64-70 | `6379f763e834373b60746288111b5e84b605e6f2ef2472cff9b5d92ba951df4c` |
| E26 | `src/xrpld/app/main/Application.cpp` | 1323-1335 | absent in rippled (`Load all ledgers that are present in the db`: 0 hits in src/xrpld/app/main/Application.cpp) | `ad95eaa5a9d0b2093c07aeb1202bfb6c9f196bfe6052a33fd54f7167b83d63c1` |
| E27 | `src/xrpld/app/tx/detail/Change.cpp` | 344-350 | rippled `src/xrpld/app/tx/detail/Change.cpp` 314-320 | `29cb123428fc99b86c425472bc2af0429c645133aa5f2bd6173249f4969161cd` |
| E28 | `include/xrpl/protocol/detail/transactions.macro` | 1131-1150 | absent in rippled (`ttVALIDATOR_VOTE`: 0 hits in include/xrpl/protocol/detail/transactions.macro) | `13a00e96c85c7716fb99ee77f6edf11dc81f8cba97b629a3c016d5633c95dd93` |
| E29 | `include/xrpl/protocol/detail/ledger_entries.macro` | 510-530 | rippled `include/xrpl/protocol/detail/ledger_entries.macro` 511-515 | `a24a1fb59b0556934c676c43b752398b34cc3db5c10785520f7b06b3fb01dbf8` |
| E30 | `src/xrpld/app/tx/detail/Change.cpp` | 548-560 | absent in rippled (`applyValidatorVote`: 0 hits in src/xrpld/app/tx/detail/Change.cpp) | `bd489475f3c4eae0a808c41beef5b57961881cef67129a712b1cef9c76b88f5c` |
| E31 | `src/xrpld/app/tx/detail/Transactor.cpp` | 190-215 | rippled `src/xrpld/app/tx/detail/Transactor.cpp` 189-195 | `4f6f329a59241c7e5d87882ea791af25e729a38da94f9d3260f77c0058b02433` |
| E32 | `include/xrpl/protocol/detail/sfields.macro` | 348-349 | absent in rippled (`sfExclusionAdd`: 0 hits in include/xrpl/protocol/detail/sfields.macro) | `8a0ffd52739f3e10113b712fd32ec45eed8fea70c263662b07a3b50b14750c31` |
| E33 | `include/xrpl/protocol/Protocol.h` | 236-238 | absent in rippled (`maxExclusionListSize`: 0 hits in include/xrpl/protocol/Protocol.h) | `0666ba8a87a078565604f93b0c3cdbe39eb05b05bb5c963e2b2533adb4341892` |
| E34 | `include/xrpl/protocol/detail/features.macro` | 45-46 | rippled `include/xrpl/protocol/detail/features.macro` 42-46 | `3ea773c673f75d9683461619c8f60a4124790f26dc4904980f1dbbdf64c51298` |
| E35 | `include/xrpl/protocol/detail/features.macro` | 47-100 | rippled `include/xrpl/protocol/detail/features.macro` 42-100 | `9b71ecba0855fd0728693a91b54a112b5567a5aaaaae6eff61be5f3ca076c8f4` |
| E36 | `include/xrpl/basics/MathUtilities.h` | 26-60 | absent in rippled (`checkedAdd`: 0 hits in include/xrpl/basics/MathUtilities.h) | `d81fd086052c1ae7986225eaa07dfb12a4797dee4936b0c4eb20777f1e2a3f6a` |
| E37 | `src/libxrpl/ledger/View.cpp` | 2476-2482 | rippled `src/libxrpl/ledger/View.cpp` 2475-2480 | `5eb68644434f3eb65ed70e0b59dd37bb15d12f6ff2753512e0685355813ea9af` |
| E38 | `src/xrpld/app/paths/detail/Steps.h` | 526-575 | absent in rippled (`checkedStepAdd`: 0 hits in src/xrpld/app/paths/detail/Steps.h) | `bbbde67af0b1c5809f2012c795c5af6c9ca7c44f1e4c37e4413189638352df37` |
| E39 | `src/xrpld/app/tx/detail/InvariantCheck.h` | 121-126 | rippled `src/xrpld/app/tx/detail/InvariantCheck.h` 121-124 | `9a1cb45a80a0d000f8f820e828413335cfcb9c688f6589f488530dd46d01c4a6` |
| E40 | `src/xrpld/app/tx/detail/InvariantCheck.cpp` | 1066-1072 | rippled `src/xrpld/app/tx/detail/InvariantCheck.cpp` 1063-1068 | `ebf2e79119874419a5def5f488fea9b46748d8f8a76ee4afc5b70187528bef2d` |
| E41 | `src/libxrpl/protocol/STObject.cpp` | 240-290 | rippled `src/libxrpl/protocol/STObject.cpp` 233-250 | `2a81c9d87a9405cad8729f22942ea0890fb620dd6ac8055d8439e37d1cc070f4` |
| E42 | `src/libxrpl/protocol/Serializer.cpp` | 230-250 | rippled `src/libxrpl/protocol/Serializer.cpp` 230-248 | `269e800bf244c72862ec0859a7cc155a301ffcb317afec7d0024ef2be1fd5912` |
| E43 | `include/xrpl/protocol/STParsedJSON.h` | 29-34 | rippled `include/xrpl/protocol/STParsedJSON.h` 26-32 | `6c282cce6e4d6fd68023019d0aa67659764201011f4cb19af28e1771f738ed88` |
| E44 | `src/xrpld/app/main/Application.cpp` | 1295-1307 | absent in rippled (`ValidatorVoteTracker`: 0 hits in src/xrpld/app/main/Application.cpp) | `27382bb72f6c3fbdf997ecac7790befa84e69956c80d9e90ce2a6cd957e13851` |
