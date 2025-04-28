# ILSP ATHENARC ASEP Anonymization Service

## REST API call
```bash
curl -X 'POST' \
  'http://10.6.115.15:8000/anonymize' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "text": "Ονομάζομαι Νίκος Νικολόπουλος, το email μου είναι nnikolopoulos@example.gr, και η διεύθυνσή μου είναι Παπανικολή 56."
}'
```

## Response with anonymization_id

```bash
{
  "anonymization_id": "61947cc1-3007-4f11-9956-48c88ba4f3a7"
}
```

## Collect results with anonymization_id


```bash
curl -X 'GET' \
  'http://10.6.115.15:8000/anonymize/61947cc1-3007-4f11-9956-48c88ba4f3a7' \
  -H 'accept: application/json'
```  

## Results

```bash
{
  "anonymization_id": "61947cc1-3007-4f11-9956-48c88ba4f3a7",
  "status": "SUCCESS",
  "result": [
    {
      "full_text": "Ονομάζομαι Νίκος Νικολόπουλος, το email μου είναι nnikolopoulos@example.gr, και η διεύθυνσή μου είναι Παπανικολή 56.",
      "masked": "Ονομάζομαι {{PERSON}}, το email μου είναι {{EMAIL_ADDRESS}}, και η διεύθυνσή μου είναι {{ADDRESS}}",
      "spans": [
        {
          "entity_type": "PERSON",
          "entity_value": "Νίκος Νικολόπουλος",
          "start_position": 11,
          "end_position": 29
        },
        {
          "entity_type": "EMAIL_ADDRESS",
          "entity_value": "nnikolopoulos@example.gr",
          "start_position": 50,
          "end_position": 74
        },
        {
          "entity_type": "ADDRESS",
          "entity_value": "Παπανικολή 56.",
          "start_position": 102,
          "end_position": 116
        }
      ]
    }
  ]
}
```