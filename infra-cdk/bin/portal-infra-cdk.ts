#!/usr/bin/env node
import "source-map-support/register";
import * as cdk from "aws-cdk-lib";
import { AirbyteStack } from "../lib/core/airbyte-infra";
import { DataIngestionDagsterStack } from "../lib/core/data-ingestion-wm-infra";
import { DatabaseStack } from "../lib/core/databases";
import { EKSResourcesStack } from "../lib/core/eks-resources";
import { ChatterBakendStack } from "../lib/core/chatter-backend";
import { PortalExperienceStack } from "../lib/core/portal-experience-infra";
import { GrafanaStack } from "../lib/devtools/grafana";

const adminAccountId = "...";
const devAccountId = "...";
const prdAccountId = "...";
const taAccountId = "...";
const primaryRegion = "us-east-1";
const secondaryRegion = "us-west-2";

const app = new cdk.App();

const account = process.env.CDK_DEFAULT_ACCOUNT;
const region = process.env.CDK_DEFAULT_REGION;

if (account === undefined) {
  throw new Error(`CDK_DEFAULT_ACCOUNT is not defined`);
}
if (region === undefined) {
  throw new Error("CDK_DEFAULT_REGION is not defined");
}
console.log(`account: ${account} region:${region}`);

if (account == prdAccountId) {
  // --------------------------------------------
  // old prod Stack(s)
  // --------------------------------------------
  // new DataIngestionDagsterStack(app, "DataIngestionDagsterStack", {
  //   env: { account: prdAccountId, region: primaryRegion },
  //   pipelineStage: "prod",
  // });
  // new DatabaseStack(app, "DatabaseStack", {
  //   env: { account: prdAccountId, region: primaryRegion },
  //   pipelineStage: "prod",
  // });
  // new PortalExperienceStack(app, "PortalExperienceStack", {
  //   env: { account: prdAccountId, region: primaryRegion },
  //   pipelineStage: "prod",
  // });

  new EKSResourcesStack(app, "prod-EksResourceStack", {
    env: { account: prdAccountId, region: primaryRegion },
    pipelineStage: "prod",
  });

  new DatabaseStack(app, "prod-airbyte-DatabaseStack", {
    env: { account: prdAccountId, region: primaryRegion },
    pipelineStage: "prod-airbyte",
  });

  // --------------------------------------------
  // prod-v2 Stack(s)
  // --------------------------------------------
  // new DataIngestionDagsterStack(app, "prod-v2-DataIngestionDagsterStack", {
  //   env: { account: prdAccountId, region: primaryRegion },
  //   pipelineStage: "prod-v2",
  // });
  new DatabaseStack(app, "prod-v2-DatabaseStackv2", {
    env: { account: prdAccountId, region: primaryRegion },
    pipelineStage: "prod-v2",
  });

  new DatabaseStack(app, "prod-px-database", {
    env: { account: prdAccountId, region: primaryRegion },
    pipelineStage: "prod-px",
  });
  // new PortalExperienceStack(app, "prod-v2-PortalExperienceStack", {
  //   env: { account: prdAccountId, region: primaryRegion },
  //   pipelineStage: "prod-v2",
  // });
  // new AirbyteStack(app, "prod-v2-AirbyteStack", {
  //   env: { account: prdAccountId, region: primaryRegion },
  //   pipelineStage: "prod-v2",
  // });
} else if (account == devAccountId) {
  // --------------------------------------------
  // dev-v2 Stack(s)
  // --------------------------------------------
  new EKSResourcesStack(app, "dev-EksResourceStack", {
    env: { account: devAccountId, region: secondaryRegion },
    pipelineStage: "dev",
  });

  // Old ECS Setup
  // new DataIngestionDagsterStack(app, "dev-v2-DataIngestionDagsterStack", {
  //   env: { account: devAccountId, region: secondaryRegion },
  //   pipelineStage: "dev-v2",
  // });

  // new DatabaseStack(app, "dev-v2-DatabaseStack", {
  //   env: { account: devAccountId, region: secondaryRegion },
  //   pipelineStage: "dev-v2",
  // });

  // new PortalExperienceStack(app, "dev-v2-PortalExperienceStack", {
  //   env: { account: devAccountId, region: secondaryRegion },
  //   pipelineStage: "dev-v2",
  // });

  new DatabaseStack(app, "dev-DatabaseStack", {
    env: { account: devAccountId, region: secondaryRegion },
    pipelineStage: "dev",
  });

  new DatabaseStack(app, "dev-airbyte-DatabaseStack", {
    env: { account: devAccountId, region: secondaryRegion },
    pipelineStage: "dev-airbyte",
  });


  // Dev database for data team testing
  new DatabaseStack(app, "dev-data-DatabaseStack", {
    env: { account: devAccountId, region: secondaryRegion },
    pipelineStage: "dev-data",
  });

  // --------------------------------------------
  // dev xlaunch Stack(s)
  // --------------------------------------------
  new DatabaseStack(app, "dev-px-database", {
    env: { account: devAccountId, region: secondaryRegion },
    pipelineStage: "dev-px",
  });


  // --------------------------------------------
  // QA Stack(s)
  // --------------------------------------------
  // old ECS setup
  // new DataIngestionDagsterStack(app, "qa-v2-DataIngestionDagsterStack", {
  //   env: { account: devAccountId, region: secondaryRegion },
  //   pipelineStage: "qa-v2",
  // });

  // new DatabaseStack(app, "qa-v2-DatabaseStack", {
  //   env: { account: devAccountId, region: secondaryRegion },
  //   pipelineStage: "qa-v2",
  // });

  // new PortalExperienceStack(app, "qa-v2-PortalExperienceStack", {
  //   env: { account: devAccountId, region: secondaryRegion },
  //   pipelineStage: "qa-v2",
  // });

  // QA databases
  // new DatabaseStack(app, "qa-eks-DatabaseStack", {
  //   env: { account: devAccountId, region: secondaryRegion },
  //   pipelineStage: "qa",
  // });

  // new DatabaseStack(app, "qa2-eks-DatabaseStack", {
  //   env: { account: devAccountId, region: secondaryRegion },
  //   pipelineStage: "qa2",
  // });

  new DatabaseStack(app, "qa1-px-database", {
    env: { account: devAccountId, region: secondaryRegion },
    pipelineStage: "qa1-px",
  });

  new DatabaseStack(app, "qa2-px-database", {
    env: { account: devAccountId, region: secondaryRegion },
    pipelineStage: "qa2-px",
  });
} 
//////////////////////////////////////////////////
// Talent Agency Setup
//////////////////////////////////////////////////
else if (account == taAccountId) {

  new DatabaseStack(app, "qa-ta-database", {
    env: { account: taAccountId, region: primaryRegion },
    pipelineStage: "qa-ta",
  });

  new ChatterBakendStack(app, "qa-chatter-backend-cluster", {
    env: { account: taAccountId, region: primaryRegion },
    pipelineStage: "qa",
  });

  // prod setup
  new DatabaseStack(app, "prod-chatter-database", {
    env: { account: taAccountId, region: primaryRegion },
    pipelineStage: "prod-chatter",
  });
  new ChatterBakendStack(app, "prod-chatter-backend-cluster", {
    env: { account: taAccountId, region: primaryRegion },
    pipelineStage: "prod",
  });

} else {
  throw new Error("Account not recognized");
}
