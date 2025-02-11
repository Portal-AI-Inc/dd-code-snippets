# infra-cdk
This repo has changes for new infrastructure using AWS CDK.

*NOTE:* There are some areas set to `undefined` if `prod` is used in order to manage the existing production setup.

## Setup 
#### Install npm packages
```npm install```

#### Setup AWS Credentials
Get AWS Access Keys and setup dev and prod in different profiles in `~/.aws`


## CDK Commands
```
# List CDK Stacks
cdk --profile dev ls

# Diff for changes for stack
cdk --profile dev diff ExampleStackName

# Deploy new stack or to existing for changes
cdk --profile dev deploy ExampleStackName

# Delete a Stack and it's infrastucture
cdk --profile dev destroy ExampleStackName

```