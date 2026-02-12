The generated code for this experiment is available in [skills-test-with-terraform](https://github.com/giwankim/skills-test-with-terraform/tree/main).

## Skills
Skills are a method of context engineering. A skill contains descriptions of additional resources, instructions, documentation, scripts, and related assets that an LLM can load on demand when relevant to the task. See, for example, [Anthropic's skills](https://github.com/anthropics/skills) and [OpenAI's skills](https://github.com/openai/skills).

## Agent skills
To test the usefulness of skills, I gave Claude Code and Codex the same prompt: once with [terraform-skill](https://github.com/antonbabenko/terraform-skill/tree/master) and once with vanilla Claude Code. I then evaluated both outputs with Codex against the guidelines prescribed by the skill.

The test involved one-shot generation of Terraform code to provision AWS infrastructure. I chose this task because I wanted to see how well agent skills transfer best practices (or "sensible defaults," as Martin Fowler would put it).

### Method
For each task, I ran the same prompt with and without the skill, compared the generated outputs, and evaluated them against the skill guidance and cloud provider best-practice references.

## "Trough of disillusionment" 😢
This phase showed that early confidence from simpler results did not consistently hold for more complex scenarios.

I was initially very happy with the generated results. My first attempt was a simple S3 module with some enterprise niceties, and Claude Code seemed to pass those tests with flying colors.

I was not an expert Terraform user, but based on general software design principles and a quick review of Terraform materials, I got the impression that the best practices described by the skill were being applied.

Next, I asked the agent to generate a three-tier architecture with a load balancer, container orchestration layer, and database, including appropriate networking. At that point, I realized I may have gotten carried away by my initial excitement.

The first issue I ran into was that, despite installing the skill and giving a clearly relevant prompt, the skill often failed to trigger. A related discussion appears in this Vercel post: [AGENTS.md Outperforms Skills in Vercel's Agent Evals](https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals).

Second, even when the skill triggered as expected, not all of the skill's guidelines were followed in the generated code. This suggested that, for now, an engineer in the loop was still required to steer agents toward the desired outcome.

## S3 Module

### Prompt
I gave the following prompt to Claude Code:

```
Create a Terraform module that provisions an S3 bucket. Set up a testing strategy, including native Terraform tests and a GitHub Actions CI pipeline.
```

### Setup
I intentionally left the prompt under-specified since I was interested in finding out how the coding agent resolved ambiguity and what its defaults were.

I manually invoked the skill through the `/` command.

### Evaluation
Finally, I asked Claude Code to evaluate both outputs against [HashiCorp Recommended Practices](https://developer.hashicorp.com/terraform/cloud-docs/recommended-practices), [AWS Best Practices](https://docs.aws.amazon.com/prescriptive-guidance/latest/terraform-aws-provider-best-practices/introduction.html), and [GCP Best Practices](https://docs.cloud.google.com/docs/terraform/best-practices/general-style-structure).

### Observations
For this simple module, the generated output initially appeared to align well with the expected practices.

## Three-tier Architecture

### Prompt
```
Create Terraform modules that provision a three-tier AWS application inside a VPC: a VPC with public and private subnets, an internet-facing ALB in the public subnets, an ECS Fargate service running in private subnets and integrated with the ALB, and an RDS database deployed in private subnets with network access from the ECS service.

Include a testing strategy using native terraform test and a GitHub Actions CI workflow.
```

### Setup
I used the same comparison setup: one run with the skill and one run without the skill.

### Evaluation
I evaluated the results against the same [HashiCorp Recommended Practices](https://developer.hashicorp.com/terraform/cloud-docs/recommended-practices), [AWS Best Practices](https://docs.aws.amazon.com/prescriptive-guidance/latest/terraform-aws-provider-best-practices/introduction.html), and [GCP Best Practices](https://docs.cloud.google.com/docs/terraform/best-practices/general-style-structure).

### Observations
As complexity increased, I observed more gaps: the skill did not always trigger, and even when it did, guideline adherence was inconsistent.

## "Slope of Enlightenment" towards the "Plateau of Productivity?"
This phase suggested that skills were still useful, but they benefited from explicit steering and engineer-in-the-loop review.
