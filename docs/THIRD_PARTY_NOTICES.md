# Third-party source and generated artifacts

Dynamo Diff's original implementation, workloads and documentation use the root MIT license. This does not relicense captured upstream source or third-party output templates.

| Retained material | Origin | License text |
|---|---|---|
| PyTorch source snapshots and source excerpts in authored-workload traces | Installed PyTorch 2.14.0, commit `08187d9e0fba026dc8217405802ab5381dc88d90` | [PyTorch license and notices](licenses/pytorch-2.14.0-LICENSE.txt) |
| Transformers source snapshots and source excerpts in the static-cache investigation | Installed Transformers 5.10.1 | [Apache License 2.0](licenses/transformers-5.10.1-LICENSE.txt) |
| tlparse report formatting and generated report bundles | Installed tlparse 0.4.3 | [BSD 3-Clause license](licenses/tlparse-0.4.3-LICENSE.txt) |

The license files above are exact copies from the respective installed distributions. Source snapshots are copied without modifying their license headers. Trace and conversion bundles come from this project's authored workloads, rather than downloaded user logs. Generated snippets can contain upstream code and remain subject to the corresponding upstream terms.

The Transformers investigation credits [issue #46421](https://github.com/huggingface/transformers/issues/46421) and its author's linked reproduction for the reported problem and early-initialization intervention. The small CPU driver and numerical checks here were authored separately; no original issue timing is claimed as a Dynamo Diff result.

Python and npm dependencies are installed separately under their own licenses. The Python wheel packages the Dynamo Diff core, and the VSIX packages the project's compiled extension code; neither bundles PyTorch, Transformers or an interpreter. The source distribution also includes the retained evidence corpus and these notices.
