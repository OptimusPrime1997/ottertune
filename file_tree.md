.
├── client
│   ├── controller
│   │   ├── build.gradle
│   │   ├── config
│   │   │   ├── sample_mysql_config.json
│   │   │   ├── sample_oracle_config.json
│   │   │   ├── sample_postgres_config.json
│   │   │   └── sample_saphana_config.json
│   │   ├── .gitignore
│   │   ├── gradle
│   │   │   └── wrapper
│   │   │       └── gradle-wrapper.properties
│   │   ├── log4j.properties
│   │   ├── README.md
│   │   ├── sample_output
│   │   │   ├── mysql
│   │   │   │   ├── knobs.json
│   │   │   │   ├── metrics_after.json
│   │   │   │   ├── metrics_before.json
│   │   │   │   └── summary.json
│   │   │   ├── oracle
│   │   │   │   ├── knobs.json
│   │   │   │   ├── metrics_after.json
│   │   │   │   ├── metrics_before.json
│   │   │   │   └── summary.json
│   │   │   ├── postgres
│   │   │   │   ├── knobs.json
│   │   │   │   ├── metrics_after.json
│   │   │   │   ├── metrics_before.json
│   │   │   │   └── summary.json
│   │   │   └── saphana
│   │   │       ├── knobs.json
│   │   │       ├── metrics_after.json
│   │   │       ├── metrics_before.json
│   │   │       └── summary.json
│   │   └── src
│   │       ├── main
│   │       │   └── java
│   │       │       └── com
│   │       │           └── controller
│   │       │               ├── collectors
│   │       │               │   ├── DBCollector.java
│   │       │               │   ├── DBParameterCollector.java
│   │       │               │   ├── MySQLCollector.java
│   │       │               │   ├── OracleCollector.java
│   │       │               │   ├── PostgresCollector.java
│   │       │               │   └── SAPHanaCollector.java
│   │       │               ├── ControllerConfiguration.java
│   │       │               ├── json_validation_schema
│   │       │               │   ├── config_schema.json
│   │       │               │   ├── schema.json
│   │       │               │   └── summary_schema.json
│   │       │               ├── Main.java
│   │       │               ├── ResultUploader.java
│   │       │               ├── types
│   │       │               │   ├── DatabaseType.java
│   │       │               │   └── JSONSchemaType.java
│   │       │               └── util
│   │       │                   ├── ClassUtil.java
│   │       │                   ├── CollectionUtil.java
│   │       │                   ├── FileUtil.java
│   │       │                   ├── json
│   │       │                   │   ├── JSONArray.java
│   │       │                   │   ├── JSONException.java
│   │       │                   │   ├── JSONObject.java
│   │       │                   │   ├── JSONStringer.java
│   │       │                   │   ├── JSONString.java
│   │       │                   │   ├── JSONTokener.java
│   │       │                   │   ├── JSONWriter.java
│   │       │                   │   └── Test.java
│   │       │                   ├── JSONSerializable.java
│   │       │                   ├── JSONUtil.java
│   │       │                   └── ValidationUtils.java
│   │       └── test
│   │           └── java
│   │               └── com
│   │                   └── controller
│   │                       └── collectors
│   │                           ├── AbstractJSONValidationTestCase.java
│   │                           ├── TestInvalidJSON.java
│   │                           ├── TestMySQLJSON.java
│   │                           ├── TestOracleJSON.java
│   │                           └── TestPostgresJSON.java
│   └── driver
│       ├── ConfParser.py
│       ├── driver_config.json
│       ├── fabfile.py
│       ├── knobs
│       │   ├── oracle.json
│       │   └── postgres-96.json
│       ├── LatencyUDF.py
│       ├── lhs.py
│       ├── lhs.sh
│       ├── oracleScripts
│       │   ├── awrOracle.sh
│       │   ├── restoreOracle.sh
│       │   ├── shutdownOracle.sh
│       │   ├── snapshotOracle.sh
│       │   └── startupOracle.sh
│       └── upload_batch.py
├── docker
│   ├── createadmin.py
│   ├── credentials.py
│   ├── docker-compose.test.yml
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── Dockerfile.base-centos-7
│   ├── Dockerfile.base-ubuntu-18.04
│   ├── Dockerfile.test
│   ├── .dockerignore
│   ├── start.sh
│   └── wait-for-it.sh
├── .dockerignore
├── .git
│   ├── branches
│   ├── config
│   ├── description
│   ├── HEAD
│   ├── hooks
│   │   ├── applypatch-msg.sample
│   │   ├── commit-msg.sample
│   │   ├── fsmonitor-watchman.sample
│   │   ├── post-update.sample
│   │   ├── pre-applypatch.sample
│   │   ├── pre-commit.sample
│   │   ├── prepare-commit-msg.sample
│   │   ├── pre-push.sample
│   │   ├── pre-rebase.sample
│   │   ├── pre-receive.sample
│   │   └── update.sample
│   ├── index
│   ├── info
│   │   └── exclude
│   ├── logs
│   │   ├── HEAD
│   │   └── refs
│   │       ├── heads
│   │       │   └── master
│   │       └── remotes
│   │           └── origin
│   │               └── HEAD
│   ├── objects
│   │   ├── info
│   │   └── pack
│   │       ├── pack-0d8d116999c495309a9d5b94c8a73cce51dca316.idx
│   │       └── pack-0d8d116999c495309a9d5b94c8a73cce51dca316.pack
│   ├── packed-refs
│   └── refs
│       ├── heads
│       │   └── master
│       ├── remotes
│       │   └── origin
│       │       └── HEAD
│       └── tags
├── .gitignore
├── LICENSE
├── README.md
├── script
│   ├── formatting
│   │   ├── config
│   │   │   ├── google_checks.xml
│   │   │   ├── pycodestyle
│   │   │   └── pylintrc
│   │   └── formatter.py
│   ├── git-hooks
│   │   └── pre-commit
│   ├── query_and_get.py
│   └── validators
│       └── source_validator.py
├── server
│   ├── analysis
│   │   ├── base.py
│   │   ├── cluster.py
│   │   ├── constraints.py
│   │   ├── factor_analysis.py
│   │   ├── gp.py
│   │   ├── gp_tf.py
│   │   ├── __init__.py
│   │   ├── lasso.py
│   │   ├── preprocessing.py
│   │   ├── tests
│   │   │   ├── __init__.py
│   │   │   ├── test_cluster.py
│   │   │   ├── test_constraints.py
│   │   │   ├── test_gpr.py
│   │   │   └── test_preprocessing.py
│   │   └── util.py
│   └── website
│       ├── beat.sh
│       ├── celery.sh
│       ├── config
│       │   ├── .gitignore
│       │   └── postgresql.conf
│       ├── django.sh
│       ├── fabfile.py
│       ├── .gitignore
│       ├── LICENSE
│       ├── manage.py
│       ├── README.md
│       ├── requirements.txt
│       ├── script
│       │   ├── controller_simulator
│       │   │   ├── data_generator.py
│       │   │   ├── .gitignore
│       │   │   ├── samples
│       │   │   │   ├── knobs.json
│       │   │   │   ├── metrics_after.json
│       │   │   │   ├── metrics_before.json
│       │   │   │   └── summary.json
│       │   │   └── upload_data.py
│       │   ├── fix_permissions.py
│       │   ├── fixture_generators
│       │   │   ├── knob_identification
│       │   │   │   ├── create_ranked_knobs.py
│       │   │   │   ├── .gitignore
│       │   │   │   └── postgres-96_m3xlarge_ranked_knobs.json
│       │   │   ├── knob_settings
│       │   │   │   ├── oracle
│       │   │   │   │   ├── create_knob_settings.py
│       │   │   │   │   ├── oracle_knobs.json
│       │   │   │   │   └── oracle.txt
│       │   │   │   └── postgres_9.6
│       │   │   │       ├── create_knob_settings.py
│       │   │   │       ├── .gitignore
│       │   │   │       ├── postgres-96_knobs.json
│       │   │   │       └── settings.csv
│       │   │   ├── metric_settings
│       │   │   │   ├── oracle
│       │   │   │   │   ├── create_metric_settings.py
│       │   │   │   │   ├── oracle_metrics.json
│       │   │   │   │   └── oracle.txt
│       │   │   │   └── postgres_9.6
│       │   │   │       ├── create_metric_settings.py
│       │   │   │       ├── .gitignore
│       │   │   │       ├── metrics_sample.json
│       │   │   │       ├── pg96_database_stats.csv
│       │   │   │       ├── pg96_global_stats.csv
│       │   │   │       ├── pg96_index_stats.csv
│       │   │   │       ├── pg96_table_stats.csv
│       │   │   │       └── postgres-96_metrics.json
│       │   │   └── workload_characterization
│       │   │       ├── create_pruned_metrics.py
│       │   │       ├── .gitignore
│       │   │       └── postgres-96_m3xlarge_pruned_metrics.json
│       │   ├── installation
│       │   │   ├── bootstrap.sh
│       │   │   ├── .gitignore
│       │   │   └── Vagrantfile
│       │   └── upload
│       │       ├── upload_batch.py
│       │       └── upload.py
│       ├── tests
│       │   ├── __init__.py
│       │   ├── runner.py
│       │   ├── test_files
│       │   │   ├── sample_knobs.json
│       │   │   ├── sample_metrics_end.json
│       │   │   ├── sample_metrics_start.json
│       │   │   └── sample_summary.json
│       │   ├── test_parser.py
│       │   ├── test_tasks.py
│       │   ├── test_upload.py
│       │   ├── test_utils.py
│       │   ├── test_views.py
│       │   └── utils.py
│       └── website
│           ├── admin.py
│           ├── fixtures
│           │   ├── dbms_catalog.json
│           │   ├── myrocks-5.6_knobs.json
│           │   ├── myrocks-5.6_metrics.json
│           │   ├── oracle_knobs.json
│           │   ├── oracle_metrics.json
│           │   ├── postgres-92_knobs.json
│           │   ├── postgres-92_metrics.json
│           │   ├── postgres-93_knobs.json
│           │   ├── postgres-93_metrics.json
│           │   ├── postgres-94_knobs.json
│           │   ├── postgres-94_metrics.json
│           │   ├── postgres-96_knobs.json
│           │   ├── postgres-96_m3xlarge_pruned_metrics.json
│           │   ├── postgres-96_m3xlarge_ranked_knobs.json
│           │   ├── postgres-96_metrics.json
│           │   ├── test_user.json
│           │   ├── test_user_sessions.json
│           │   └── test_website.json
│           ├── forms.py
│           ├── __init__.py
│           ├── migrations
│           │   ├── 0001_initial.py
│           │   ├── 0002_enable_compression.py
│           │   ├── 0003_background_task_optimization.py
│           │   ├── 0004_load_initial_data.py
│           │   ├── 0005_adding_session_knob.py
│           │   ├── 0006_added_algorithm_selection.py
│           │   └── __init__.py
│           ├── models.py
│           ├── parser
│           │   ├── base.py
│           │   ├── __init__.py
│           │   ├── myrocks.py
│           │   ├── oracle.py
│           │   ├── parser.py
│           │   └── postgres.py
│           ├── set_default_knobs.py
│           ├── settings
│           │   ├── common.py
│           │   ├── constants.py
│           │   ├── credentials_TEMPLATE.py
│           │   ├── .gitignore
│           │   └── __init__.py
│           ├── static
│           │   ├── css
│           │   │   ├── base.css
│           │   │   ├── bootstrap.min.css -> themes/bootstrap-flatly.min.css
│           │   │   ├── bootstrap-select.min.css
│           │   │   ├── jquery.dataTables.css
│           │   │   ├── style.css
│           │   │   └── themes
│           │   │       ├── bootstrap-darkly.min.css
│           │   │       ├── bootstrap-default.min.css
│           │   │       ├── bootstrap-flatly.min.css
│           │   │       └── bootstrap-sandstone.min.css
│           │   ├── fonts
│           │   │   ├── glyphicons-halflings-regular.eot
│           │   │   ├── glyphicons-halflings-regular.svg
│           │   │   ├── glyphicons-halflings-regular.ttf
│           │   │   ├── glyphicons-halflings-regular.woff
│           │   │   └── glyphicons-halflings-regular.woff2
│           │   ├── img
│           │   │   ├── ajax-loader.gif
│           │   │   ├── glyphicons-halflings.png
│           │   │   ├── glyphicons-halflings-white.png
│           │   │   ├── logo.png
│           │   │   ├── otter.jpg
│           │   │   ├── sort_asc.png
│           │   │   ├── sort_both.png
│           │   │   └── sort_desc.png
│           │   └── js
│           │       ├── benchmark_bar.js
│           │       ├── bootstrap.min.js
│           │       ├── bootstrap-select.js.map
│           │       ├── bootstrap-select.min.js
│           │       ├── common.js
│           │       ├── FixedHeader.min.js
│           │       ├── jqplot
│           │       │   ├── excanvas.min.js
│           │       │   ├── jqplot.barRenderer.min.js
│           │       │   ├── jqplot.canvasAxisLabelRenderer.min.js
│           │       │   ├── jqplot.canvasAxisTickRenderer.min.js
│           │       │   ├── jqplot.canvasTextRenderer.min.js
│           │       │   ├── jqplot.categoryAxisRenderer.min.js
│           │       │   ├── jqplot.cursor.min.js
│           │       │   ├── jqplot.dateAxisRenderer.min.js
│           │       │   ├── jqplot.highlighter.min.js
│           │       │   ├── jqplot.logAxisRenderer.min.js
│           │       │   ├── jqplot.pointLabels.min.js
│           │       │   ├── jquery.jqplot.min.css
│           │       │   └── jquery.jqplot.min.js
│           │       ├── jquery-1.10.2.min.js
│           │       ├── jquery-1.7.2.min.js
│           │       ├── jquery.address-1.5.min.js
│           │       ├── jquery.dataTables.min.js
│           │       ├── jquery.jqpagination.min.js
│           │       ├── jquery-migrate-1.2.1.min.js
│           │       ├── result10.js
│           │       └── timeline.js
│           ├── tasks
│           │   ├── async_tasks.py
│           │   ├── __init__.py
│           │   └── periodic_tasks.py
│           ├── templates
│           │   ├── 404.html
│           │   ├── base.html
│           │   ├── change_password.html
│           │   ├── dbms_data.html
│           │   ├── dbms_reference.html
│           │   ├── edit_knobs.html
│           │   ├── edit_project.html
│           │   ├── edit_session.html
│           │   ├── edit_workload.html
│           │   ├── home_projects.html
│           │   ├── login.html
│           │   ├── project_sessions.html
│           │   ├── result.html
│           │   ├── session.html
│           │   ├── signup.html
│           │   ├── task_status.html
│           │   └── workload.html
│           ├── templatetags
│           │   ├── __init__.py
│           │   └── util_functions.py
│           ├── types.py
│           ├── urls.py
│           ├── utils.py
│           ├── views.py
│           └── wsgi.py
└── .travis.yml

87 directories, 311 files
