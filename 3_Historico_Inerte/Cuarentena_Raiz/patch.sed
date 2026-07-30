s/PROJECT_ID: cortex-babylon-60/PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}/g
s/WORKLOAD_IDENTITY_PROVIDER: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}/WORKLOAD_IDENTITY_PROVIDER: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}\n  SERVICE_ACCOUNT: ${{ secrets.GCP_SERVICE_ACCOUNT }}/g
s/service_account: "c5-deployer@cortex-babylon-60.iam.gserviceaccount.com"/service_account: ${{ env.SERVICE_ACCOUNT }}/g
