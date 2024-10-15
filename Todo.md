This is a todo list for what need to figure out with the faasflow orchestrator

# The current status of the job

Find out how the FaaSFlow works and take the experiment part out from it


# The default FaaSflow Spawning process:

FaaSFlow_orch/test/asplos/schedule_overhead/run.py -> src/workflow_manager/gateway.py -> workflow_manager/proxy.py -> workflow_manager/workersp.py

trigger_function_local / trigger_function_remote
run_function

# The parser works:
the workflow is now parsed

Setting the grouping and scheduling algorithm