# Pixel-wise Anomaly Detection in Complex Driving Scenes
This repository is the paper implementation for Pixel-wise Anomaly Detection in Complex Driving Scenes ([Link](https://arxiv.org/abs/2103.05445)). 

![Alt text](display_images/methodology.png?raw=true "Methodology")

### Requirements

To install the requirements:
```pip install -r requirements_demo.txt```


### Pretrained Weights

Links to different pretrained weights:
1) For the full framework :  https://drive.google.com/file/d/1FX4_df0SkmhnU_1ymTRDKHuueXlV4W4X/view?usp=sharing
2) For the light version :   
3) Link to original author's model : http://robotics.ethz.ch/~asl-datasets/Dissimilarity/models.tar

The above pretrained weights zip folder also contains the pretrained weights of segmentation and synthesis models. Additionally, you can refer to the original repositories.


### Datasets 
The repository uses the Cityscapes Dataset [4] as the basis of the training data for the dissimilarity model. 
To download the dataset please register and follow the instructions here: https://www.cityscapes-dataset.com/downloads/.

Then, we need to pre-process the images in order to get the predicted entropy, distance, perceptual difference, synthesis, and semantic maps.
For this please provide the original cityscapes instanceids, labelids and the original images. Add the paths to these directories in the test_options.py under options folder.
Also provide pretrained weights of segmentation and synthesis.

For making the data, run the following:

1) segmentation.py (makes the data from the semantic predictions)

2) create_unknown.py (uses the ground truth semantic maps)

- This is the link to dataset of full framework (provided in the original author's repo) : http://robotics.ethz.ch/~asl-datasets/Dissimilarity/data_processed.tar
- Link to dataset of light data : https://www.kaggle.com/shashwatnaidu07/light-data-synboost
- Link to dataset of w/o data generator: https://www.kaggle.com/shashwatnaidu/synboostwo-data-generator

(For main model and light framework you can find labels in the Dataset)


### Training 
In order to trained the dissimilarity network, we have to do the following:

1) Modify the necessary parameters in the configuration file `image_dissimilarity/configs/train/default_configuration.yaml`. 
More importanly, modify the folder paths for each dataset to your local path. In order to get the required data for training, please 
refer to the Dataset section. Also add the deatils of wandb in the configuration file.
2) ```
   cd image_dissimilarity
   train.py --config configs/train/default_configuration.yaml
   ```

### Evaluation
To Run ensemble(with grid search):
1) For FS Static: 
```
cd image_dissimilarity
test_ensemble.py --config configs/test/fs_static_configuration.yaml 
test_ensemble.py --config configs/test/fs_lost_found_configuration.yaml 
```

2) For Lost and Found : 
```
cd image_dissimilarity
test_ensemble.py --config configs/test/fs_lost_found_configuration.yaml 
```

To Run testing directly with fixed weights(this also saves the final prediction images where the anomaly has been segmented):
1) For FS Static: 
```
cd image_dissimilarity
test_ensemble.py --config configs/test/fs_static_configuration.yaml 
``` 
2) For Lost and Found : 
```
cd image_dissimilarity
test_ensemble.py --config configs/test/fs_lost_found_configuration.yaml 
```
### Results

![alt text](https://github.com/manideep1108/synboost/blob/master/display_images/Comapring%20oututs%20of%20ours%20and%20authors.jpeg?raw=true)
The above image compares author's final predictions (2nd column from right) with our predictions(last column)


### Framework Light Version 
The original paper discussed the implementation of a lighter version in order to demostrate the generalization ability of the network to different
synthesis and segmentation networks (even with lower performance).

In the repository, we include the code and pre-trained model used for this lighter version. However, compatiblity with `demo.py` is still not supported. 
We have also provided link to light version's dataset (refer to dataset section).


### Google Colab Demo Notebook
A demo of the anomaly detection pipeline can be found here: https://colab.research.google.com/drive/1HQheunEWYHvOJhQQiWbQ9oHXCNi9Frfl?usp=sharing#scrollTo=gC-ViJmm23eM

### ONNX Conversion 

In order to convert all three models into `.onnx`, it is neccesary to update the `symbolic_opset11.py` file from the
original `torch` module installation. The reason for this is that `torch==1.4.0` does not have compatibility for `im2col`
which is neccesary for the synthesis model. 

Simply copy the `symbolic_opset11.py` from this repository and replace the one from the torch module inside your project environment. 
The file is located `/Path/To/Enviroment/lib/python3.7/site-packages/torch/onnx`

### Notes 

- The branch `fishyscapes_package` includes the code as a package specifically made for Fishyscapes submission.
In ther to get the class for the detector simply `from test_fishy_torch import AnomalyDetector`.

- The branch 'pytorch_lightning' includes the code for the full framework using pytorch lightning.



## References
[1] Learning to Predict Layout-to-image Conditional Convolutions for Semantic Image Synthesis.
Xihui Liu, Guojun Yin, Jing Shao, Xiaogang Wang and Hongsheng Li.

[2] Improving Semantic Segmentation via Video Propagation and Label Relaxation
Yi Zhu1, Karan Sapra, Fitsum A. Reda, Kevin J. Shih, Shawn Newsam, Andrew Tao, Bryan Catanzaro.

[3] https://github.com/lxtGH/Fast_Seg

[4] High-resolution image synthesis and semantic manipulation with conditional gans.
Ting-Chun Wang, Ming-Yu Liu, Jun-Yan Zhu, Andrew Tao, Jan Kautz, and Bryan Catanzaro. 

[5] The cityscapes dataset for semantic urban scene understanding. 
Marius Cordts, Mohamed Omran, Sebastian Ramos, Timo Rehfeld, Markus Enzweiler, Rodrigo Benenson, Uwe Franke, Stefan Roth, and Bernt Schiele
