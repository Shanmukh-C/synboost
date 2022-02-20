from data.cityscapes_dataset import CityscapesDataset
from torch.utils.data import DataLoader
from models.dissimilarity_model import DissimNet, DissimNetPrior, DissimNetPriorEndtoEnd
import torch.nn as nn
from torch.optim.lr_scheduler import ReduceLROnPlateau
import torch
softmax = torch.nn.Softmax(dim=1)
import pytorch_lightning as pl
import numpy as np
from util import trainer_util, metrics
import os


h = 256
w = 512   #should figure this out for now I have hard coded this



class SynboostDataModule(pl.LightningDataModule):
    def __init__(self,config):
        super().__init__()
    
        self.config= config

        self.train_dataset = CityscapesDataset(**self.config["train_dataloader"]['dataset_args'])

        self.validation_dataset = CityscapesDataset(**self.config["val_dataloader"]['dataset_args'])
        self.test_dataset1 = CityscapesDataset(**self.config["test_dataloader1"]['dataset_args'])
        self.test_dataset2 = CityscapesDataset(**self.config["test_dataloader2"]['dataset_args'])
        self.test_dataset3 = CityscapesDataset(**self.config["test_dataloader3"]['dataset_args'])

    def train_dataloader(self):
        return DataLoader(self.train_dataset, **self.config["train_dataloader"]['dataloader_args'])
    
    def val_dataloader(self):
        return [ DataLoader(self.validation_dataset, **self.config["val_dataloader"]['dataloader_args']),
            DataLoader(self.test_dataset1, **self.config["test_dataloader1"]['dataloader_args']),
            DataLoader(self.test_dataset2, **self.config["test_dataloader2"]['dataloader_args']),
            DataLoader(self.test_dataset3, **self.config["test_dataloader3"]['dataloader_args']),
        ]



class Synboost_trainer(pl.LightningModule):
    def __init__(self,config):
        super().__init__()
        
        self.val_loss = 0
        self.config = config

        self.data_module = SynboostDataModule(self.config)   
        self.test_loader1_size = len(self.data_module.val_dataloader()[1])
        self.test_loader2_size = len(self.data_module.val_dataloader()[2])
        self.test_loader3_size = len(self.data_module.val_dataloader()[3])
        
        self.flat_pred = [torch.zeros(h*w*self.test_loader1_size).cuda(),torch.zeros(h*w*self.test_loader2_size).cuda(),torch.zeros(h*w*self.test_loader3_size).cuda()]
        self.flat_labels = [torch.zeros(h*w*self.test_loader1_size).cuda(),torch.zeros(h*w*self.test_loader2_size).cuda(),torch.zeros(h*w*self.test_loader3_size).cuda()]
        
        if config['model']['prior']:
            if config['model']['endtoend']:
                self.diss_model = DissimNetPriorEndtoEnd(**config['model'])
            else:
                self.diss_model = DissimNetPrior(**config['model'])
        else:
            self.diss_model = DissimNet(**config['model'])

        if self.config['training_strategy']['class_weight']:
            if not self.config['training_strategy']['class_weight_cityscapes']:
                if self.config['train_dataloader']['dataset_args']['void']:
                    label_path = os.path.join(self.config['train_dataloader']['dataset_args']['dataroot'], 'labels_with_void_no_ego/')
                else:
                    label_path = os.path.join(self.config['train_dataloader']['dataset_args']['dataroot'], 'labels/')
                    
                full_loader = trainer_util.loader(label_path, batch_size='all')
                print('Getting class weights for cross entropy loss. This might take some time.')
                class_weights = trainer_util.get_class_weights(full_loader, num_classes=2)
                #print("class weights are")
                #print(class_weights)
                torch.save(class_weights,"class_weights.pth")
            else:
                if self.config['train_dataloader']['dataset_args']['void']:
                    class_weights = [1.54843156, 8.03912212]
                else:
                    class_weights = [1.46494611, 16.5204619]
            print('Using the following weights for each respective class [0,1]:', class_weights)
            self.criterion = nn.CrossEntropyLoss(ignore_index=255, weight=torch.FloatTensor(class_weights))
        else:
            self.criterion = nn.CrossEntropyLoss(ignore_index=255)

        self.save_hyperparameters()  


    def  training_step(self,batch,batch_idx):
        #iter_counter.record_one_iteration()
        original = batch['original']
        semantic = batch['semantic']
        synthesis = batch['synthesis']
        label = batch['label']
        
        # Training
        if self.config['model']['prior']:
            entropy = batch['entropy']
            mae = batch['mae']
            distance = batch['distance']
            predictions = self.diss_model(original, synthesis, semantic, entropy, mae, distance)
            #print(predictions.get_device())  #for debugging
            #print(label.type(torch.LongTensor).squeeze(dim=1).get_device().cuda())
            loss = self.criterion(predictions, label.type(torch.LongTensor).squeeze(dim=1).cuda())
            
        else:
            predictions = self.diss_model(original, synthesis, semantic)
            loss = self.criterion(predictions, label.type(torch.LongTensor).squeeze(dim=1))
        
        #self.log("train_iter_losss",loss)
        self.log_dict(
            {"train_iter_losss" : loss},
            on_step=True,
            on_epoch=True,
            prog_bar=True,
        )

        return loss
        # if opts.wandb:
        #     wandb.log({"Loss_iter_train": model_loss, "train_idx": idx_train})
        # iter+=1
        # idx_train +=1
            

    # def training_epoch_end(self, training_step_outputs):
    #     print("Training Loss after epoch %f is : "% (self.trainer.current_epoch), sum(training_step_outputs)/len(training_step_outputs))  #self.trainer.current_epoch
    #     self.log('avg_loss_train', sum(training_step_outputs)/len(training_step_outputs))



    def validation_step(self, batch, batch_idx, dataloader_idx=0):
        original = batch['original']
        semantic = batch['semantic']
        synthesis = batch['synthesis']   
        label = batch['label']
        
        if self.config['model']['prior']:
            entropy = batch['entropy']
            mae = batch['mae']
            distance = batch['distance']
    
            # Evaluating
            predictions = self.diss_model(original, synthesis, semantic, entropy, mae, distance)
            loss = self.criterion(predictions, label.type(torch.LongTensor).squeeze(dim=1).cuda())
        else:
            predictions = self.diss_model(original, synthesis, semantic)
            loss = self.criterion(predictions, label.type(torch.LongTensor).squeeze(dim=1).cuda())


        if(dataloader_idx== 1 or dataloader_idx== 2 or dataloader_idx== 3 ):
            outputs = softmax(predictions)
            (softmax_pred, predictions) = torch.max(outputs, dim=1)
            self.flat_pred[dataloader_idx-1][batch_idx * w * h:batch_idx * w * h + w * h] = torch.flatten(outputs[:, 1, :, :])
            self.flat_labels[dataloader_idx-1][batch_idx * w * h:batch_idx * w * h + w * h] = torch.flatten(label)
        
        self.log_dict(
            {"val_loss" : loss},
            on_step=False,
            on_epoch=True
        )

        return loss       


    def validation_epoch_end(self, validation_step_outputs, dataloader_idx=0):
        for idx in range(3):
            results = metrics.get_metrics(self.flat_labels[idx].cpu().detach().numpy(), self.flat_pred[idx].cpu().detach().numpy())
            log_dic = {"mAP%d"%(idx+1): results['AP'], "FPR@95TPR%d"%(idx+1): results['FPR@95%TPR'], "AU_ROC%d"%(idx+1): results['auroc']}
            self.log_dict(log_dic)

        self.flat_pred = [torch.zeros(h*w*self.test_loader1_size).cuda(),torch.zeros(h*w*self.test_loader2_size).cuda(),torch.zeros(h*w*self.test_loader3_size).cuda()]
        self.flat_labels = [torch.zeros(h*w*self.test_loader1_size).cuda(),torch.zeros(h*w*self.test_loader2_size).cuda(),torch.zeros(h*w*self.test_loader3_size).cuda()]
    

    def configure_optimizers(self):
        if self.config['optimizer']['algorithm'] == 'SGD':
                optimizer = torch.optim.SGD(self.diss_model.parameters(), lr=self.config['optimizer']['parameters']['lr'],
                                        weight_decay=self.config['optimizer']['parameters']['weight_decay'],)
        elif self.config['optimizer']['algorithm'] == 'Adam':
                optimizer = torch.optim.Adam(self.diss_model.parameters(),
                                        lr=self.config['optimizer']['parameters']['lr'],
                                        weight_decay=self.config['optimizer']['parameters']['weight_decay'],
                                        betas=(self.config['optimizer']['parameters']['beta1'], self.config['optimizer']['parameters']['beta2']))
        else:
                raise NotImplementedError

        return {
            "optimizer": optimizer,
            "lr_scheduler": {
                "scheduler": ReduceLROnPlateau(optimizer, 'min', patience=self.config['optimizer']['parameters']['patience'], factor=self.config['optimizer']['parameters']['factor']),
                "monitor": "val_loss/dataloader_idx_0" ,     #should check if I should change the variable name
                "interval": "epoch",
                "frequency": 1 
                # If "monitor" references validation metrics, then "frequency" should be set to a
                # multiple of "trainer.check_val_every_n_epoch".
            },  #should resolve this temporaririly stopped it
        }


