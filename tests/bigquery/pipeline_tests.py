#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2017 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License
# is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied. See the License for the specific language governing permissions and limitations under
# the License.

import google
import google.auth
import google.datalab.contrib.bigquery.commands._bigquery as bq
import mock
import re
import unittest


class TestCases(unittest.TestCase):

  test_input_config = {
    'path': 'test_path',
    'table': 'test_table',
    'schema': 'test_schema',
    'mode': 'append',
    'format': 'csv',
    'csv': {
      'delimiter': ';',
      'skip': 9,
      'strict': False,
      'quote': '"'
    },
  }

  test_pipeline_config = {
    'input': test_input_config,
  }

  @staticmethod
  def _create_context():
    project_id = 'test'
    creds = mock.Mock(spec=google.auth.credentials.Credentials)
    return google.datalab.Context(project_id, creds)

  @mock.patch('google.datalab.utils.commands.get_notebook_item')
  def test_get_pipeline_spec_from_config(self, mock_notebook_item):
    mock_notebook_item.return_value = google.datalab.bigquery.Query('foo_query_sql_string')

    # empty pipeline_spec
    with self.assertRaisesRegexp(Exception, 'Pipeline has no tasks to execute.'):
      bq._get_pipeline_spec_from_config({})

    # empty input , transformation, output as path
    pipeline_config = {
      'transformation': {
        'query': 'foo_query'
      },
      'output': {
        'path': 'foo_table'
      }
    }

    expected = {
      'tasks': {
        'bq_pipeline_execute_task': {
          'sql': u'foo_query_sql_string',
          'type': 'pydatalab.bq.execute'
        },
        'bq_pipeline_extract_task': {
          'path': 'foo_table',
          'type': 'pydatalab.bq.extract',
          'up_stream': ['bq_pipeline_execute_task']
        }
      }
    }

    self.assertDictEqual(bq._get_pipeline_spec_from_config(pipeline_config), expected)

    # input as path, transformation, output as path
    pipeline_config = {
      'input': {
        'path': 'foo_path',
        'data_source': 'foo_data_source',
      },
      'transformation': {
        'query': 'foo_query'
      },
      'output': {
        'path': 'foo_table'
      }
    }

    expected = {
      'tasks': {
        'bq_pipeline_execute_task': {
          'sql': u'foo_query_sql_string',
          'data_source': 'foo_data_source',
          'path': 'foo_path',
          'type': 'pydatalab.bq.execute'
        },
        'bq_pipeline_extract_task': {
          'path': 'foo_table',
          'type': 'pydatalab.bq.extract',
          'up_stream': ['bq_pipeline_execute_task']
        }
      }
    }

    self.assertDictEqual(bq._get_pipeline_spec_from_config(pipeline_config), expected)

    # input as path->table, transformation, output as path
    pipeline_config = {
      'input': {
        'path': 'foo_path',
        'table': 'foo_table_1'
      },
      'transformation': {
        'query': 'foo_query'
      },
      'output': {
        'path': 'foo_path_2'
      }
    }

    expected = {
      'tasks': {
        'bq_pipeline_load_task': {
          'type': 'pydatalab.bq.load',
          'path': 'foo_path',
          'table': 'foo_table_1',
        },
        'bq_pipeline_execute_task': {
          'sql': u'foo_query_sql_string',
          'type': 'pydatalab.bq.execute',
          'up_stream': ['bq_pipeline_load_task'],
        },
        'bq_pipeline_extract_task': {
          'path': 'foo_path_2',
          'type': 'pydatalab.bq.extract',
          'up_stream': ['bq_pipeline_execute_task']
        }
      }
    }

    # input as table, transformation, output as path
    pipeline_config = {
      'input': {
        'table': 'foo_table_1'
      },
      'transformation': {
        'query': 'foo_query'
      },
      'output': {
        'path': 'foo_path_2'
      }
    }

    expected = {
      'tasks': {
        'bq_pipeline_execute_task': {
          'sql': u'foo_query_sql_string',
          'type': 'pydatalab.bq.execute',
        },
        'bq_pipeline_extract_task': {
          'path': 'foo_path_2',
          'type': 'pydatalab.bq.extract',
          'up_stream': ['bq_pipeline_execute_task']
        }
      }
    }

    self.assertDictEqual(bq._get_pipeline_spec_from_config(pipeline_config), expected)

    # input as table, transformation, output as table
    pipeline_config = {
      'input': {
        'table': 'foo_table_1'
      },
      'transformation': {
        'query': 'foo_query'
      },
      'output': {
        'table': 'foo_table_1'
      }
    }

    expected = {
      'tasks': {
        'bq_pipeline_execute_task': {
          'sql': u'foo_query_sql_string',
          'type': 'pydatalab.bq.execute',
          'table': 'foo_table_1'
        },
      }
    }

    self.assertDictEqual(bq._get_pipeline_spec_from_config(pipeline_config), expected)

    # input as table, no transformation, output as path
    pipeline_config = {
      'input': {
        'table': 'foo_table'
      },
      'output': {
        'path': 'foo_path'
      }
    }

    expected = {
      'tasks': {
        'bq_pipeline_extract_task': {
          'type': 'pydatalab.bq.extract',
          'path': 'foo_path',
          'table': 'foo_table'
        },
      }
    }

    self.assertDictEqual(bq._get_pipeline_spec_from_config(pipeline_config), expected)

    # output only; this should be identical to the above
    pipeline_config = {
      'output': {
        'table': 'foo_table',
        'path': 'foo_path'
      }
    }

    expected = {
      'tasks': {
        'bq_pipeline_extract_task': {
          'type': 'pydatalab.bq.extract',
          'path': 'foo_path',
          'table': 'foo_table'
        },
      }
    }

    self.assertDictEqual(bq._get_pipeline_spec_from_config(pipeline_config), expected)

    # input as path, no transformation, output as table
    pipeline_config = {
      'input': {
        'path': 'foo_path'
      },
      'output': {
        'table': 'foo_table'
      }
    }

    expected = {
      'tasks': {
        'bq_pipeline_load_task': {
          'type': 'pydatalab.bq.load',
          'path': 'foo_path',
          'table': 'foo_table'
        },
      }
    }

    self.assertDictEqual(bq._get_pipeline_spec_from_config(pipeline_config), expected)

    # input only; this should be identical to the above
    pipeline_config = {
      'input': {
        'path': 'foo_path',
        'table': 'foo_table'
      },
    }

    self.assertDictEqual(bq._get_pipeline_spec_from_config(pipeline_config), expected)

    # only transformation
    pipeline_config = {
      'transformation': {
        'query': 'foo_query'
      },
    }

    expected = {
      'tasks': {
        'bq_pipeline_execute_task': {
          'sql': u'foo_query_sql_string',
          'type': 'pydatalab.bq.execute',
        },
      }
    }

    self.assertDictEqual(bq._get_pipeline_spec_from_config(pipeline_config), expected)

  def test_get_load_parameters(self):
    actual_load_config = bq._get_load_parameters(TestCases.test_input_config, None, None)
    expected_load_config = {
      'type': 'pydatalab.bq.load',
      'path': 'test_path',
      'table': 'test_table',
      'schema': 'test_schema',
      'mode': 'append',
      'format': 'csv',
      'csv_options': {'delimiter': ';', 'quote': '"', 'skip': 9, 'strict': False},
    }
    self.assertDictEqual(actual_load_config, expected_load_config)

    # Table is present in output config
    input_config = {
      'path': 'test_path',
      'format': 'csv',
      'csv': {'delimiter': ';', 'quote': '"', 'skip': 9, 'strict': False},
    }
    output_config = {
      'table': 'test_table',
      'schema': 'test_schema',
      'mode': 'append',
    }
    actual_load_config = bq._get_load_parameters(input_config, None, output_config)
    self.assertDictEqual(actual_load_config, expected_load_config)

    # Path is absent
    input_config = {
      'table': 'test_table',
      'schema': 'test_schema'
    }
    actual_load_config = bq._get_load_parameters(input_config, None, None)
    self.assertIsNone(actual_load_config)

    # Path and table are absent
    input_config = {
      'schema': 'test_schema'
    }
    actual_load_config = bq._get_load_parameters(input_config, None, None)
    self.assertIsNone(actual_load_config)

    # Table is absent
    input_config = {
      'path': 'test_path',
      'schema': 'test_schema'
    }
    actual_load_config = bq._get_load_parameters(input_config, None, None)
    self.assertIsNone(actual_load_config)

  def test_get_extract_parameters(self):
    output_config = {
      'path': 'test_path',
      'table': 'test_table',
    }
    actual_extract_config = bq._get_extract_parameters('foo_execute_task', None, None,
                                                       output_config)
    expected_extract_config = {
      'type': 'pydatalab.bq.extract',
      'up_stream': ['foo_execute_task'],
      'path': 'test_path',
      'table': 'test_table',
    }

    self.assertDictEqual(actual_extract_config, expected_extract_config)

    input_config = {
      'table': 'test_table',
    }
    output_config = {
      'path': 'test_path',
    }
    actual_extract_config = bq._get_extract_parameters('foo_execute_task', input_config, None,
                                                       output_config)
    self.assertDictEqual(actual_extract_config, expected_extract_config)

  @mock.patch('google.datalab.utils.commands.get_notebook_item')
  def test_get_execute_parameters(self, mock_notebook_item):
    mock_notebook_item.return_value = google.datalab.bigquery.Query(
        'SELECT @column FROM publicdata.samples.wikipedia where endpoint=@endpoint')

    transformation_config = {
      'query': 'foo_query'
    }
    output_config = {
      'table': 'foo_table',
      'mode': 'foo_mode'
    }
    parameters_config = [
      {
        'type': 'STRING',
        'name': 'endpoint',
        'value': 'Interact2'
      },
      {
        'type': 'INTEGER',
        'name': 'column',
        'value': '1234'
      }
    ]
    actual_execute_config = bq._get_execute_parameters('foo_load_task', {}, transformation_config,
                                                       output_config, parameters_config)
    expected_execute_config = {
      'type': 'pydatalab.bq.execute',
      'up_stream': ['foo_load_task'],
      'sql': 'SELECT @column FROM publicdata.samples.wikipedia where endpoint=@endpoint',
      'table': 'foo_table',
      'mode': 'foo_mode',
      'parameters': parameters_config
    }
    self.assertDictEqual(actual_execute_config, expected_execute_config)

    # With empty output config
    actual_execute_config = bq._get_execute_parameters('foo_load_task', {}, transformation_config,
                                                       {}, parameters_config)
    expected_execute_config = {
      'type': 'pydatalab.bq.execute',
      'up_stream': ['foo_load_task'],
      'sql': 'SELECT @column FROM publicdata.samples.wikipedia where endpoint=@endpoint',
      'parameters': parameters_config
    }

    input_config = TestCases.test_input_config
    input_config['data_source'] = 'foo_data_source'
    self.assertDictEqual(actual_execute_config, expected_execute_config)
    actual_execute_config = bq._get_execute_parameters('foo_load_task', TestCases.test_input_config,
                                                       transformation_config, {}, parameters_config)
    expected_execute_config = {
      'type': 'pydatalab.bq.execute',
      'up_stream': ['foo_load_task'],
      'sql': 'SELECT @column FROM publicdata.samples.wikipedia where endpoint=@endpoint',
      'data_source': 'foo_data_source',
      'path': 'test_path',
      'schema': 'test_schema',
      'source_format': 'csv',
      'csv_options': {'delimiter': ';', 'quote': '"', 'skip': 9, 'strict': False},
      'parameters': parameters_config
    }

    self.assertDictEqual(actual_execute_config, expected_execute_config)

  @mock.patch('google.datalab.Context.default')
  @mock.patch('google.datalab.utils.commands.notebook_environment')
  @mock.patch('google.datalab.utils.commands.get_notebook_item')
  @mock.patch('google.datalab.bigquery.Table.exists')
  @mock.patch('google.datalab.bigquery.commands._bigquery._get_table')
  @mock.patch('google.cloud.storage.Blob')
  @mock.patch('google.cloud.storage.Client')
  @mock.patch('google.cloud.storage.Client.get_bucket')
  def test_pipeline_cell_golden(self, mock_client_get_bucket, mock_client, mock_blob_class,
                                mock_get_table, mock_table_exists, mock_notebook_item,
                                mock_environment, mock_default_context):
    table = google.datalab.bigquery.Table('project.test.table')
    mock_get_table.return_value = table
    mock_table_exists.return_value = True
    context = TestCases._create_context()
    mock_default_context.return_value = context
    mock_client_get_bucket.return_value = mock.Mock(spec=google.cloud.storage.Bucket)
    mock_blob = mock_blob_class.return_value

    env = {
      'endpoint': 'Interact2',
      'job_id': '1234',
      'input_table_format': 'cloud-datalab-samples.httplogs.logs_%(ds)s',
      'output_table_format': 'cloud-datalab-samples.endpoints.logs_%(ds)s'
    }
    mock_notebook_item.return_value = google.datalab.bigquery.Query(
        'SELECT @column FROM `{0}` where endpoint=@endpoint'.format(env['input_table_format']))

    mock_environment.return_value = env
    args = {'name': 'bq_pipeline_test'}
    # TODO(rajivpb): The references to foo_query need to be resolved.
    cell_body = """
            emails: foo1@test.com,foo2@test.com
            schedule:
                start: 2009-05-05T22:28:15Z
                end: 2009-05-06T22:28:15Z
                interval: '@hourly'
            input:
                path: gs://bucket/cloud-datalab-samples-httplogs_%(ds)s
                table: $input_table_format
                csv:
                  header: True
                  strict: False
                  quote: '"'
                  skip: 5
                  delimiter: ','
                schema:
                  - name: col1
                    type: int64
                    mode: NULLABLE
                    description: description1
                  - name: col2
                    type: STRING
                    mode: required
                    description: description1
            transformation:
                query: foo_query
            output:
                path: gs://bucket/cloud-datalab-samples-endpoints_%(ds)s.csv
                table: $output_table_format
            parameters:
                - name: endpoint
                  type: STRING
                  value: $endpoint
                - name: column
                  type: INTEGER
                  value: $job_id
    """

    output = bq._pipeline_cell(args, cell_body)

    pattern = re.compile("""
import datetime
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.contrib.operators.bigquery_operator import BigQueryOperator
from airflow.contrib.operators.bigquery_table_delete_operator import BigQueryTableDeleteOperator
from airflow.contrib.operators.bigquery_to_bigquery import BigQueryToBigQueryOperator
from airflow.contrib.operators.bigquery_to_gcs import BigQueryToCloudStorageOperator
from airflow.contrib.operators.gcs_to_bq import GoogleCloudStorageToBigQueryOperator
from google.datalab.contrib.bigquery.operators._bq_load_operator import LoadOperator
from google.datalab.contrib.bigquery.operators._bq_execute_operator import ExecuteOperator
from google.datalab.contrib.bigquery.operators._bq_extract_operator import ExtractOperator
from datetime import timedelta
from pytz import timezone

default_args = {
    'owner': 'Datalab',
    'depends_on_past': False,
    'email': \['foo1@test.com', 'foo2@test.com'\],
    'start_date': datetime.datetime.strptime\('2009-05-05T22:28:15', '%Y-%m-%dT%H:%M:%S'\).replace\(tzinfo=timezone\('UTC'\)\),
    'end_date': datetime.datetime.strptime\('2009-05-06T22:28:15', '%Y-%m-%dT%H:%M:%S'\).replace\(tzinfo=timezone\('UTC'\)\),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta\(minutes=1\),
}

dag = DAG\(dag_id='bq_pipeline_test', schedule_interval='@hourly', default_args=default_args\)

bq_pipeline_execute_task = ExecuteOperator\(task_id='bq_pipeline_execute_task_id', parameters=(.*), sql='SELECT @column FROM `cloud-datalab-samples.httplogs.logs_{{ ds_nodash }}` where endpoint=@endpoint', table='cloud-datalab-samples.endpoints.logs_{{ ds_nodash }}', dag=dag\)
bq_pipeline_extract_task = ExtractOperator\(task_id='bq_pipeline_extract_task_id', path='gs://bucket/cloud-datalab-samples-endpoints_{{ ds_nodash }}.csv', table='cloud-datalab-samples.endpoints.logs_{{ ds_nodash }}', dag=dag\)
bq_pipeline_load_task = LoadOperator\(task_id='bq_pipeline_load_task_id', csv_options=(.*), path='gs://bucket/cloud-datalab-samples-httplogs_{{ ds_nodash }}', schema=(.*), table='cloud-datalab-samples.httplogs.logs_{{ ds_nodash }}', dag=dag\)
bq_pipeline_execute_task.set_upstream\(bq_pipeline_load_task\)
bq_pipeline_extract_task.set_upstream\(bq_pipeline_execute_task\)
""")  # noqa

    self.assertIsNotNone(pattern.match(output))

    # String that follows the "parameters=", for the execute operator.
    actual_parameter_dict_str = pattern.match(output).group(1)
    self.assertIn("'type': 'STRING'", actual_parameter_dict_str)
    self.assertIn("'name': 'endpoint'", actual_parameter_dict_str)
    self.assertIn("'value': 'Interact2'", actual_parameter_dict_str)
    self.assertIn("'type': 'INTEGER'", actual_parameter_dict_str)
    self.assertIn("'name': 'column'", actual_parameter_dict_str)
    self.assertIn("'value': '1234'", actual_parameter_dict_str)

    # String that follows the "csv_options=", for the load operator.
    actual_csv_options_dict_str = pattern.match(output).group(2)
    self.assertIn("'header': True", actual_csv_options_dict_str)
    self.assertIn("'delimiter': ','", actual_csv_options_dict_str)
    self.assertIn("'skip': 5", actual_csv_options_dict_str)
    self.assertIn("'strict': False", actual_csv_options_dict_str)
    self.assertIn("'quote': '\"'", actual_csv_options_dict_str)

    # String that follows the "schema=", i.e. the list of dicts.
    actual_schema_str = pattern.match(output).group(3)
    self.assertIn("'type': 'int64'", actual_schema_str)
    self.assertIn("'mode': 'NULLABLE'", actual_schema_str)
    self.assertIn("'name': 'col1'", actual_schema_str)
    self.assertIn("'description': 'description1'", actual_schema_str)
    self.assertIn("'type': 'STRING'", actual_schema_str)
    self.assertIn("'mode': 'required'", actual_schema_str)
    self.assertIn("'name': 'col2'", actual_schema_str)
    self.assertIn("'description': 'description1'", actual_schema_str)

    mock_blob.upload_from_string.assert_called_with(output)
