"""Response contracts shared by the published job routes."""
NULLABLE_TIME = {"type":["string","null"],"format":"date-time"}
JOB = {
    "type":"object",
    "required":["id","operation","state","created_at","started_at","completed_at","expires_at","attempts","error","status_url","result"],
    "properties":{
        "id":{"type":"string"},"operation":{"type":"string","enum":["grayscale","compress","merge","pdf-to-text"]},
        "state":{"type":"string","enum":["queued","running","succeeded","failed","canceled","expired"]},
        "created_at":{"type":"string","format":"date-time"},"started_at":NULLABLE_TIME,"completed_at":NULLABLE_TIME,"expires_at":NULLABLE_TIME,
        "attempts":{"type":"integer","minimum":0},"status_url":{"type":"string"},
        "error":{"type":["object","null"],"properties":{"code":{"type":"string"},"message":{"type":"string"}}},
        "result":{"type":["object","null"],"properties":{
            "url":{"type":"string"},"bytes":{"type":"integer"},"media_type":{"type":"string"},"filename":{"type":"string"}}}}}
DELETION = {"type":"object","required":["id","state","deletion_pending"],"properties":{
    "id":{"type":"string"},"state":{"type":"string","const":"canceled"},"deletion_pending":{"type":"boolean"}}}
TEXT_RESULT = {"type":"object","required":["text","pages","characters"],"properties":{
    "text":{"type":"string"},"characters":{"type":"integer"},"warning":{"type":"string"},
    "pages":{"type":"array","items":{"type":"object","required":["page","text"],"properties":{"page":{"type":"integer"},"text":{"type":"string"}}}}}}


def json_response(schema: dict, description: str) -> dict:
    return {"description":description,"content":{"application/json":{"schema":schema}}}
