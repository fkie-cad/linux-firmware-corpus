# notebooks

This folder holds all notebooks that were used in our paper. Feel free to interactively explore the data contained here!

## Install dependenices

```sh
./prepare
```

## Run Jupyter Lab

```sh
./jupyter
```

## Folder Structure Deciphered


```plain
.
├── figures                                                              
│   ├── f10_corpus_architectures.pdf                                     # corpus architecture distribution figure
│   ├── f1_challenges.pdf                                                # firmware corpus creation challenges from Sec. II (InkScape)
│   ├── f2_requirements.pdf                                              # Corpus Requirements from Sec. III (InkScape)
│   ├── f3_literature_methodology.pdf                                    # Literature Methodology from Sec. IV (InkScape)
│   ├── f4_relative_degree_of_measure_documentation_across_papers.pdf    # measure score results from Sec. IV
│   ├── f5_requirement_score_literature_tricolor.pdf                     # requirement score results from Sec. IV
│   ├── f7_corpus_release_dates.pdf                                      # corpus release date distribution figure
│   ├── f8_corpus_classes.pdf                                            # corpus class distribution figure
│   └── f9_corpus_linux_banners.pdf                                      # linux banner analysis figure
├── jupyter                                                              # run jupyter lab
├── notebooks                                                            # holds all Jupyter Notebooks
│   ├── IV_literature_review.ipynb                                       # literature review analysis from our paper (Sec. IV)
│   ├── V_lfwc.ipynb                                                     # LFwC meta data analysis from our paper (Sec. V)
│   ├── _mask_lfwc.ipynb                                                 # (internal use, for documentation: mask full lfwc versions)
│   └── html_output                                                      # pre-rendered versions of the jupyter notebooks
│       ├── IV_literature_review.html                                    # IV_literature_review.ipynb
│       ├── V_lfwc.html                                                  # V_lfwc.ipynb
│       └── _mask_lfwc.html                                              # _mask_lfwc.ipynb
├── prepare                                                              # install dependencies script for the notebooks. Works with Ubuntu.
├── public_data                                                          # publicly shared data sets
│   ├── lfwc-failed-masked.csv                                           # masked version of lfwc-failed with all replication data removed. Request full version at Zenodo.
│   ├── lfwc-masked.csv                                                  # masked version of lfwc-full with all replication data removed. Request full version at Zenodo.
│   ├── literature_overview.csv                                          # raw data for Tab. I in the paper
│   ├── literature_results.csv                                           # raw data for Tab. II in the paper
│   └── routersploit_mapping.json                                        # routersploit ground truth mapping to lfwc samples
└── requirements.txt                                                     # python requirements
```

## Additional Resources

- [Jupyter Documentation & Getting Started](https://docs.jupyter.org/en/latest/#)
- [pandas Documentation & Getting Started](https://pandas.pydata.org/docs/getting_started/index.html)

