# Inject Container Webhook

Based on configmaps it will inject Init or regular containers to the pod

## Pre-requisites

This needs `cert-manager` to generate and renew the tls certificates

### Customizations

Apply customizations to the yaml files inside the **deploy** folder as needed

1. Find and replace all instances of `tools` with something else if you want to install in a different namespace
2. Modify the `certificate.yaml` file as needed
   1. Install certmanager and apply the `selfsigned.yaml` (if `selfsigned-issuer` doesn't exist)
   2. Alternatively setup a ClusterIssuer/Issuer using [cert-manager](https://cert-manager.io/docs/concepts/issuer/) and edit the `certificate.yaml` with customizations
   3. Replace `tools` with alternative namespace if installing elsewhere
3. Modify the `deployment.yaml` file as needed with the following options
   1. Change environment variables as needed (see [Available Variables below](#available-variables))
   2. Change the replica and resources values as needed depending on how many targeted pods your evironment might have (the defaults are probably fine for anything under 10k)
4. Modify the `mutatingwebhook.yaml` as needed
   1. Remove the `namespaceSelector` lines if you want all pods targeted (careful as this will include itself/kube-system)
   2. Change the `namespaceSelector` to select the namespaces you want to target (see [namespaceSelector docs](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/#matching-requests-namespaceselector))

### Apply Kubernetes Files

Apply in the following order after making any needed modifications

```bash
kubectl apply -f selfsigned.yaml  # this should be already in the cluster as a global object and not linked to this solution
kubectl apply -f certificate.yaml
kubectl apply -f service-account.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f configmap.yaml
kubectl apply -f mutatingwebhook.yaml
```

s

## Available Variables

These variables can be set when running the docker image to customize the functionality

| Variable      | Default               | Description                                                                                                       |
| ------------- | --------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **LOG_LEVEL** | DEBUG,INFO,WARN,ERROR | If set to DEBUG will enable additional output including a dump of input and output objects for debugging purposes |
