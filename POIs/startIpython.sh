#!/bin/bash
ssh -i "dataGather.pem" -L 8000:localhost:8888 ec2-user@ec2-52-15-236-186.us-east-2.compute.amazonaws.com
