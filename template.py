from troposphere import (Template, cloudformation, awslambda, GetAtt, Join, iam, Ref, Parameter)
from awacs.aws import Policy, Allow, Statement, Principal, Action
from alias_lambda import __version__ as lambda_version
import os

__version__ = "1.2"

def lambda_from_file(python_file):
    """
    Reads a python file and returns a awslambda.Code object
    :param python_file:
    :return:
    """
    lambda_function = []
    with open(python_file, 'r') as f:
        lambda_function.extend(f.read().splitlines())

    return awslambda.Code(ZipFile=(Join('\n', lambda_function)))


class AccountAlias(cloudformation.AWSCustomObject):
    
    resource_type = "Custom::AccountAlias"
    props = {
        'ServiceToken': (basestring, True),
        'Alias': (basestring, True)
    }


if __name__ == "__main__":
    # Instantiating the template object
    t = Template()

    t.add_description("Set an account alias".format(__version__, lambda_version))

    alias_param = t.add_parameter(Parameter(
        "Alias",
        Description ='Alias to be set',
        Type = "String",
        Default = "SomeAlias",
        ))

    lambda_role = t.add_resource(iam.Role(
        "LambdaRole",
        AssumeRolePolicyDocument=Policy(
            Version="2012-10-17",
            Statement=[
                Statement(
                    Effect=Allow,
                    Principal=Principal("Service", "lambda.amazonaws.com"),
                    Action=[Action("sts", "AssumeRole")]
                )
            ]),
        Path="/",
        Policies=[
            iam.Policy(
                PolicyName="AccessLogs",
                PolicyDocument=Policy(
                    Version="2012-10-17",
                    Statement=[
                        Statement(
                            Effect=Allow,
                            Action=[
                                Action("logs", "CreateLogGroup"),
                                Action("logs", "CreateLogStream"),
                                Action("logs", "PutLogEvents")
                            ],
                            Resource=["arn:aws:logs:*:*:*"]
                        )
                    ]
                )
            ),
            iam.Policy(
                PolicyName="saml",
                PolicyDocument=Policy(
                    Version="2012-10-17",
                    Statement=[
                        Statement(
                            Effect=Allow,
                            Action=[
                                Action("iam", "ListAccountAliases"),
                                Action("iam", "CreateAccountAlias"),
                                Action("iam", "DeleteAccountAlias")
                                ],
                            Resource=["*"]
                        )
                    ]
                )
                )
        ]
    ))

    # Fetch the correct relative path to the scale_in_protection.py lambda function
    filename = os.path.join(os.path.dirname(__file__), "alias_lambda.py")

    alias_function = t.add_resource(awslambda.Function(
        "AccountAliasFunction",
        FunctionName=Join("-", ["AccountAliasFunction", Ref("AWS::StackName")]),
        Handler="index.lambda_handler",
        Role=GetAtt(lambda_role, "Arn"),
        Runtime="python2.7",
        Timeout=300,
        MemorySize=1536,
        Code=lambda_from_file(filename),
    ))


    t.add_resource(AccountAlias(
        "AccountAlias",
        ServiceToken=GetAtt(alias_function, "Arn"),
        Alias=Ref(alias_param)
    ))
    print(t.to_json())
