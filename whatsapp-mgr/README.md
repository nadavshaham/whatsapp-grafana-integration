# WhatsApp Manager

A simple Python program designed to be used in container environments like Kubernetes and Argo Workflows. The script processes JSON input and prints it to stdout.

## Usage

The script accepts JSON input in three different ways:

### 1. Command Line Arguments

```bash
python app.py --message '{"key": "value", "another_key": "another_value"}'
```

Or using the short form:

```bash
python app.py -m '{"key": "value", "another_key": "another_value"}'
```

### 2. Environment Variables

```bash
MESSAGE_JSON='{"key": "value", "another_key": "another_value"}' python app.py
```

### 3. Standard Input (Piping)

```bash
echo '{"key": "value", "another_key": "another_value"}' | python app.py
```

## Docker Usage

Build the Docker image:

```bash
docker build -t whatsapp-mgr:latest .
```

Run using command line argument:

```bash
docker run whatsapp-mgr:latest --message '{"key": "value"}'
```

Run using environment variable:

```bash
docker run -e MESSAGE_JSON='{"key": "value"}' whatsapp-mgr:latest
```

Run using standard input:

```bash
echo '{"key": "value"}' | docker run -i whatsapp-mgr:latest
```

## Argo Workflow Example

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: whatsapp-mgr-
spec:
  entrypoint: whatsapp-process
  templates:
  - name: whatsapp-process
    inputs:
      parameters:
      - name: message
        value: '{"key": "value", "notification": "test"}'
    container:
      image: <your-ecr-repo>/whatsapp-mgr:latest
      args: ["--message", "{{inputs.parameters.message}}"]
```

Or using environment variables:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: whatsapp-mgr-
spec:
  entrypoint: whatsapp-process
  templates:
  - name: whatsapp-process
    inputs:
      parameters:
      - name: message
        value: '{"key": "value", "notification": "test"}'
    container:
      image: <your-ecr-repo>/whatsapp-mgr:latest
      env:
      - name: MESSAGE_JSON
        value: "{{inputs.parameters.message}}"
```