# devops EKS 
Eksctl, helm and services for our kubernetes cluster(s)


# Install kubctl
https://kubernetes.io/docs/tasks/tools/install-kubectl-macos/

## Configure authentication to EKS Cluster
In order to allow `kubectl` to authenticate to cluster, need to create a config file that can be done by running the following command
```
aws eks update-kubeconfig --region <region-code> --name <my-cluster>
```