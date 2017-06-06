#!/usr/bin/env python
import cfnresponse
import boto3

__version__ = "1.1"

def lambda_handler(event, context):

    try:
        alias = event['ResourceProperties']['Alias']
        iam = boto3.client('iam')

        cur_aliases = iam.list_account_aliases()['AccountAliases']
        if event['RequestType'] == 'Create' or event['RequestType'] == 'Update':
            if cur_aliases:
                for a in cur_aliases:
                    iam.delete_account_alias(AccountAlias=a)
            iam.create_account_alias(AccountAlias=alias)
            print("Setting account alias to {}".format(alias))
    except Exception as e:
        print(str(e))
        cfnresponse.send(event, context, cfnresponse.FAILED, None, "1")
    return cfnresponse.send(event, context, cfnresponse.SUCCESS, {'Alias': alias}, "1")
