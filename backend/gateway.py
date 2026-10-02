import time







from detection.detection_pipeline import run_detection



from detection.normalizer import normalize_findings







from backend.risk_engine import calculate_risk



from backend.redis_store import (

    get_history,

    save_history,

    save_pending_hitl,

    get_pending_hitl,

    delete_pending_hitl

)



from backend.policy import get_policy_decision



from backend.masking import mask_sensitive_data



from backend.ai_provider import send_to_approved_ai







from processing.pdf_processor import extract_pdf_content



from processing.docx_processor import extract_docx_content



from processing.xlsx_processor import extract_xlsx_content



from processing.pptx_processor import extract_pptx_content



from processing.image_processor import extract_image_content











def map_finding_to_docx_source(



    finding: dict,



    source_segments: list



) -> list:



    """



    Map a detector finding's character span to the



    original DOCX paragraph/table source.



    """







    start = finding.get("start")



    end = finding.get("end")







    if start is None or end is None:



        return []







    matched_sources = []







    for segment in source_segments:



        segment_start = segment["start"]



        segment_end = segment["end"]







        overlaps = (



            start < segment_end



            and end > segment_start



        )







        if overlaps:



            matched_sources.append({



                "location": segment["location"],



                "source_type": segment["source_type"],



                "source_id": segment["source_id"]



            })







    return matched_sources











def add_docx_provenance(



    findings: list,



    source_segments: list



) -> list:



    """



    Add real source provenance to DOCX findings.



    """







    enriched_findings = []







    for finding in findings:



        new_finding = dict(finding)







        matched_sources = map_finding_to_docx_source(



            finding,



            source_segments



        )







        new_finding["document_source"] = "DOCX"







        if len(matched_sources) == 1:



            source = matched_sources[0]







            new_finding["location"] = source["location"]



            new_finding["source_type"] = source["source_type"]



            new_finding["source_id"] = source["source_id"]







        elif len(matched_sources) > 1:



            new_finding["location"] = "MULTI_SOURCE"



            new_finding["source_type"] = "MULTI_SOURCE"



            new_finding["source_id"] = None



            new_finding["source_locations"] = matched_sources







        else:



            new_finding["location"] = "UNKNOWN"



            new_finding["source_type"] = "UNKNOWN"



            new_finding["source_id"] = None







        enriched_findings.append(new_finding)







    return enriched_findings











def map_finding_to_xlsx_source(



    finding: dict,



    source_segments: list



) -> list:



    """



    Map a detector finding's character span to the



    original XLSX worksheet/cell source.



    """







    start = finding.get("start")



    end = finding.get("end")







    if start is None or end is None:



        return []







    matched_sources = []







    for segment in source_segments:



        segment_start = segment["start"]



        segment_end = segment["end"]







        overlaps = (



            start < segment_end



            and end > segment_start



        )







        if overlaps:



            matched_sources.append({



                "location": segment["location"],



                "source_type": segment["source_type"],



                "source_id": segment.get("cell"),



                "sheet_name": segment.get("sheet_name"),



                "cell": segment.get("cell")



            })







    return matched_sources











def add_xlsx_provenance(



    findings: list,



    source_segments: list



) -> list:



    """



    Add real worksheet/cell provenance to XLSX findings.



    """







    enriched_findings = []







    for finding in findings:



        new_finding = dict(finding)







        matched_sources = map_finding_to_xlsx_source(



            finding,



            source_segments



        )







        new_finding["document_source"] = "XLSX"







        if len(matched_sources) == 1:



            source = matched_sources[0]







            new_finding["location"] = source["location"]



            new_finding["source_type"] = source["source_type"]



            new_finding["source_id"] = source["source_id"]



            new_finding["sheet_name"] = source["sheet_name"]



            new_finding["cell"] = source["cell"]







        elif len(matched_sources) > 1:



            new_finding["location"] = "MULTI_SOURCE"



            new_finding["source_type"] = "MULTI_SOURCE"



            new_finding["source_id"] = None



            new_finding["sheet_name"] = None



            new_finding["cell"] = None



            new_finding["source_locations"] = matched_sources







        else:



            new_finding["location"] = "UNKNOWN"



            new_finding["source_type"] = "UNKNOWN"



            new_finding["source_id"] = None



            new_finding["sheet_name"] = None



            new_finding["cell"] = None







        enriched_findings.append(new_finding)







    return enriched_findings











def map_finding_to_pptx_source(



    finding: dict,



    source_segments: list



) -> list:



    """



    Map a detector finding's character span to the



    original PPTX slide/shape source.



    """







    start = finding.get("start")



    end = finding.get("end")







    if start is None or end is None:



        return []







    matched_sources = []







    for segment in source_segments:



        segment_start = segment["start"]



        segment_end = segment["end"]







        overlaps = (



            start < segment_end



            and end > segment_start



        )







        if overlaps:



            matched_sources.append({



                "location": segment["location"],



                "source_type": segment["source_type"],



                "source_id": segment.get("source_id"),



                "slide_number": segment.get("slide_number"),



                "shape_number": segment.get("shape_number"),



                "shape_type": segment.get("shape_type")



            })







    return matched_sources











def add_pptx_provenance(



    findings: list,



    source_segments: list



) -> list:



    """



    Add real slide/shape provenance to PPTX findings.



    """







    enriched_findings = []







    for finding in findings:



        new_finding = dict(finding)







        matched_sources = map_finding_to_pptx_source(



            finding,



            source_segments



        )







        new_finding["document_source"] = "PPTX"







        if len(matched_sources) == 1:



            source = matched_sources[0]







            new_finding["location"] = source["location"]



            new_finding["source_type"] = source["source_type"]



            new_finding["source_id"] = source["source_id"]



            new_finding["slide_number"] = source["slide_number"]



            new_finding["shape_number"] = source["shape_number"]



            new_finding["shape_type"] = source["shape_type"]







        elif len(matched_sources) > 1:



            new_finding["location"] = "MULTI_SOURCE"



            new_finding["source_type"] = "MULTI_SOURCE"



            new_finding["source_id"] = None



            new_finding["slide_number"] = None



            new_finding["shape_number"] = None



            new_finding["shape_type"] = None



            new_finding["source_locations"] = matched_sources







        else:



            new_finding["location"] = "UNKNOWN"



            new_finding["source_type"] = "UNKNOWN"



            new_finding["source_id"] = None



            new_finding["slide_number"] = None



            new_finding["shape_number"] = None



            new_finding["shape_type"] = None







        enriched_findings.append(new_finding)







    return enriched_findings











def add_image_provenance(



    findings: list,



    source_segments: list



) -> list:



    """



    Add OCR provenance to image findings.







    V1 image OCR currently provides one canonical



    IMAGE OCR segment covering the extracted text.



    """







    enriched_findings = []







    for finding in findings:



        new_finding = dict(finding)







        start = finding.get("start")



        end = finding.get("end")







        matched_sources = []







        if start is not None and end is not None:



            for segment in source_segments:



                segment_start = segment["start"]



                segment_end = segment["end"]







                overlaps = (



                    start < segment_end



                    and end > segment_start



                )







                if overlaps:



                    matched_sources.append(segment)







        new_finding["document_source"] = "IMAGE"







        if len(matched_sources) == 1:



            source = matched_sources[0]







            new_finding["location"] = source["location"]



            new_finding["source_type"] = source["source_type"]



            new_finding["source_id"] = source["source_id"]







        elif len(matched_sources) > 1:



            new_finding["location"] = "MULTI_SOURCE"



            new_finding["source_type"] = "MULTI_SOURCE"



            new_finding["source_id"] = None



            new_finding["source_locations"] = matched_sources







        else:



            new_finding["location"] = "UNKNOWN"



            new_finding["source_type"] = "UNKNOWN"



            new_finding["source_id"] = None







        enriched_findings.append(new_finding)







    return enriched_findings











async def process_hitl_decision(

    session_id: str,

    decision: str

):

    """

    Process a human decision for a request

    that was previously placed into HITL review.

    """



    decision = decision.upper().strip()



    allowed_decisions = {

        "ALLOW",

        "SANITIZE_AND_SEND",

        "BLOCK"

    }



    if decision not in allowed_decisions:

        raise ValueError(

            "Invalid HITL decision. "

            "Use ALLOW, SANITIZE_AND_SEND, or BLOCK."

        )



    pending_request = await get_pending_hitl(

        session_id

    )



    if not pending_request:

        raise ValueError(

            "No pending HITL request found "

            "for this session."

        )



    original_text = pending_request.get(

        "text",

        ""

    )



    findings = pending_request.get(

        "findings",

        []

    )



    if not original_text:

        await delete_pending_hitl(session_id)

        raise ValueError(

            "Pending HITL request does not contain "

            "valid input text."

        )



    sanitized_text = None

    ai_response = None



    if decision == "ALLOW":



        ai_response = await send_to_approved_ai(

            original_text

        )



    elif decision == "SANITIZE_AND_SEND":



        sanitized_text = mask_sensitive_data(

            original_text,

            findings

        )



        ai_response = await send_to_approved_ai(

            sanitized_text

        )



    elif decision == "BLOCK":



        ai_response = None



    await delete_pending_hitl(session_id)



    return {

        "session_id": session_id,

        "decision": decision,

        "sanitized_text": sanitized_text,

        "ai_response": ai_response,

        "status": (

            "blocked"

            if decision == "BLOCK"

            else "processed"

        )

    }





async def process_text(



    text: str,



    session_id: str



):



    raw_findings = run_detection(text)







    normalized_findings = normalize_findings(



        raw_findings



    )







    history = await get_history(session_id)







    risk_result = calculate_risk(



        normalized_findings,



        history



    )







    policy_result = get_policy_decision(



        risk_result



    )







    sanitized_text = None



    ai_response = None







    decision = policy_result["decision"]







    if decision == "ALLOW":



        ai_response = await send_to_approved_ai(



            text



        )







    elif decision == "SANITIZE_AND_SEND":



        sanitized_text = mask_sensitive_data(



            text,



            normalized_findings



        )







        ai_response = await send_to_approved_ai(



            sanitized_text



        )







    elif decision == "HITL":



        await save_pending_hitl(

            session_id,

            {

                "text": text,

                "findings": normalized_findings

            }

        )



        ai_response = None



    elif decision == "BLOCK":



        ai_response = None







    current_turn = {



        "timestamp": int(time.time()),



        "isolated_risk": risk_result[



            "isolated_risk"



        ],



        "findings": [



            {



                "type": finding.get("type"),



                "confidence": finding.get(



                    "confidence",



                    1.0



                )



            }



            for finding in normalized_findings



        ]



    }







    history.append(current_turn)







    await save_history(



        session_id,



        history



    )







    return {



        "session_id": session_id,



        "input_type": "TEXT",



        "text": text,



        "findings": normalized_findings,



        "risk": risk_result,



        "policy": policy_result,



        "sanitized_text": sanitized_text,



        "ai_response": ai_response,



        "history_turns": len(history)



    }











async def process_pdf(



    pdf_path: str,



    session_id: str



):



    pdf_result = extract_pdf_content(pdf_path)







    document_text = pdf_result["text"]







    raw_findings = run_detection(



        document_text



    )







    normalized_findings = normalize_findings(



        raw_findings



    )







    pdf_findings = []







    for finding in normalized_findings:



        pdf_findings.append({



            **finding,



            "document_source": "PDF"



        })







    history = await get_history(



        session_id



    )







    risk_result = calculate_risk(



        pdf_findings,



        history



    )







    policy_result = get_policy_decision(



        risk_result



    )







    sanitized_text = None



    ai_response = None







    decision = policy_result["decision"]







    if decision == "ALLOW":



        ai_response = await send_to_approved_ai(



            document_text



        )







    elif decision == "SANITIZE_AND_SEND":



        sanitized_text = mask_sensitive_data(



            document_text,



            pdf_findings



        )







        ai_response = await send_to_approved_ai(



            sanitized_text



        )
    elif decision == "HITL":

        await save_pending_hitl(
            session_id,
            {
                "text": document_text,
                "findings": pdf_findings
            }
        )

        ai_response = None

    elif decision == "BLOCK":

        ai_response = None







    current_turn = {



        "timestamp": int(time.time()),



        "isolated_risk": risk_result[



            "isolated_risk"



        ],



        "findings": [



            {



                "type": finding.get("type"),



                "confidence": finding.get(



                    "confidence",



                    1.0



                )



            }



            for finding in pdf_findings



        ]



    }







    history.append(current_turn)







    await save_history(



        session_id,



        history



    )







    return {



        "session_id": session_id,



        "input_type": "PDF",



        "file_name": pdf_result[



            "file_name"



        ],



        "page_count": pdf_result[



            "page_count"



        ],



        "pages": pdf_result[



            "pages"



        ],



        "extracted_text": document_text,



        "findings": pdf_findings,



        "risk": risk_result,



        "policy": policy_result,



        "sanitized_text": sanitized_text,



        "ai_response": ai_response,



        "history_turns": len(history)



    }











async def process_docx(



    docx_path: str,



    session_id: str



):



    docx_result = extract_docx_content(



        docx_path



    )







    document_text = docx_result["text"]







    source_segments = docx_result[



        "source_segments"



    ]







    raw_findings = run_detection(



        document_text



    )







    normalized_findings = normalize_findings(



        raw_findings



    )







    docx_findings = add_docx_provenance(



        normalized_findings,



        source_segments



    )







    history = await get_history(



        session_id



    )







    risk_result = calculate_risk(



        docx_findings,



        history



    )







    policy_result = get_policy_decision(



        risk_result



    )







    sanitized_text = None



    ai_response = None







    decision = policy_result["decision"]







    if decision == "ALLOW":



        ai_response = await send_to_approved_ai(



            document_text



        )







    elif decision == "SANITIZE_AND_SEND":



        sanitized_text = mask_sensitive_data(



            document_text,



            docx_findings



        )







        ai_response = await send_to_approved_ai(



            sanitized_text



        )
    elif decision == "HITL":

        await save_pending_hitl(
            session_id,
            {
                "text": document_text,
                "findings": docx_findings
            }
        )

        ai_response = None

    elif decision == "BLOCK":

        ai_response = None







    current_turn = {



        "timestamp": int(time.time()),



        "isolated_risk": risk_result[



            "isolated_risk"



        ],



        "findings": [



            {



                "type": finding.get("type"),



                "confidence": finding.get(



                    "confidence",



                    1.0



                )



            }



            for finding in docx_findings



        ]



    }







    history.append(current_turn)







    await save_history(



        session_id,



        history



    )







    return {



        "session_id": session_id,



        "input_type": "DOCX",



        "file_name": docx_result[



            "file_name"



        ],



        "paragraph_count": docx_result[



            "paragraph_count"



        ],



        "table_count": docx_result[



            "table_count"



        ],



        "extracted_text": document_text,



        "source_segments": source_segments,



        "findings": docx_findings,



        "risk": risk_result,



        "policy": policy_result,



        "sanitized_text": sanitized_text,



        "ai_response": ai_response,



        "history_turns": len(history)



    }











async def process_xlsx(



    xlsx_path: str,



    session_id: str



):



    xlsx_result = extract_xlsx_content(



        xlsx_path



    )







    document_text = xlsx_result["text"]







    source_segments = xlsx_result[



        "source_segments"



    ]







    raw_findings = run_detection(



        document_text



    )







    normalized_findings = normalize_findings(



        raw_findings



    )







    xlsx_findings = add_xlsx_provenance(



        normalized_findings,



        source_segments



    )







    history = await get_history(



        session_id



    )







    risk_result = calculate_risk(



        xlsx_findings,



        history



    )







    policy_result = get_policy_decision(



        risk_result



    )







    sanitized_text = None



    ai_response = None







    decision = policy_result["decision"]







    if decision == "ALLOW":



        ai_response = await send_to_approved_ai(



            document_text



        )







    elif decision == "SANITIZE_AND_SEND":



        sanitized_text = mask_sensitive_data(



            document_text,



            xlsx_findings



        )







        ai_response = await send_to_approved_ai(



            sanitized_text



        )
    elif decision == "HITL":

        await save_pending_hitl(
            session_id,
            {
                "text": document_text,
                "findings": xlsx_findings
            }
        )

        ai_response = None

    elif decision == "BLOCK":

        ai_response = None







    current_turn = {



        "timestamp": int(time.time()),



        "isolated_risk": risk_result[



            "isolated_risk"



        ],



        "findings": [



            {



                "type": finding.get("type"),



                "confidence": finding.get(



                    "confidence",



                    1.0



                )



            }



            for finding in xlsx_findings



        ]



    }







    history.append(current_turn)







    await save_history(



        session_id,



        history



    )







    return {



        "session_id": session_id,



        "input_type": "XLSX",



        "file_name": xlsx_result[



            "file_name"



        ],



        "worksheet_count": xlsx_result[



            "worksheet_count"



        ],



        "worksheets": xlsx_result[



            "worksheets"



        ],



        "extracted_text": document_text,



        "source_segments": source_segments,



        "findings": xlsx_findings,



        "risk": risk_result,



        "policy": policy_result,



        "sanitized_text": sanitized_text,



        "ai_response": ai_response,



        "history_turns": len(history)



    }











async def process_pptx(



    pptx_path: str,



    session_id: str



):



    pptx_result = extract_pptx_content(



        pptx_path



    )







    document_text = pptx_result["text"]







    source_segments = pptx_result[



        "source_segments"



    ]







    raw_findings = run_detection(



        document_text



    )







    normalized_findings = normalize_findings(



        raw_findings



    )







    pptx_findings = add_pptx_provenance(



        normalized_findings,



        source_segments



    )







    history = await get_history(



        session_id



    )







    risk_result = calculate_risk(



        pptx_findings,



        history



    )







    policy_result = get_policy_decision(



        risk_result



    )







    sanitized_text = None



    ai_response = None







    decision = policy_result["decision"]







    if decision == "ALLOW":



        ai_response = await send_to_approved_ai(



            document_text



        )







    elif decision == "SANITIZE_AND_SEND":



        sanitized_text = mask_sensitive_data(



            document_text,



            pptx_findings



        )







        ai_response = await send_to_approved_ai(



            sanitized_text



        )
    elif decision == "HITL":

        await save_pending_hitl(
            session_id,
            {
                "text": document_text,
                "findings": pptx_findings
            }
        )

        ai_response = None

    elif decision == "BLOCK":

        ai_response = None







    current_turn = {



        "timestamp": int(time.time()),



        "isolated_risk": risk_result[



            "isolated_risk"



        ],



        "findings": [



            {



                "type": finding.get("type"),



                "confidence": finding.get(



                    "confidence",



                    1.0



                )



            }



            for finding in pptx_findings



        ]



    }







    history.append(current_turn)







    await save_history(



        session_id,



        history



    )







    return {



        "session_id": session_id,



        "input_type": "PPTX",



        "file_name": pptx_result[



            "file_name"



        ],



        "slide_count": pptx_result[



            "slide_count"



        ],



        "slides": pptx_result[



            "slides"



        ],



        "extracted_text": document_text,



        "source_segments": source_segments,



        "findings": pptx_findings,



        "risk": risk_result,



        "policy": policy_result,



        "sanitized_text": sanitized_text,



        "ai_response": ai_response,



        "history_turns": len(history),



        "original_file_name": pptx_result[



            "file_name"



        ],



        "processing_message": "PPTX processed successfully."



    }











async def process_image(



    image_path: str,



    session_id: str



):



    """



    Process an image through the same security pipeline



    used by the document processors.







    IMAGE



      ↓



    Tesseract OCR



      ↓



    Detection



      ↓



    Provenance



      ↓



    Risk



      ↓



    Policy



      ↓



    Allow / Sanitize / Block



    """







    image_result = extract_image_content(



        image_path



    )







    document_text = image_result["text"]







    source_segments = image_result[



        "source_segments"



    ]







    raw_findings = run_detection(



        document_text



    )







    normalized_findings = normalize_findings(



        raw_findings



    )







    image_findings = add_image_provenance(



        normalized_findings,



        source_segments



    )







    history = await get_history(



        session_id



    )







    risk_result = calculate_risk(



        image_findings,



        history



    )







    policy_result = get_policy_decision(



        risk_result



    )







    sanitized_text = None



    ai_response = None







    decision = policy_result["decision"]







    if decision == "ALLOW":



        ai_response = await send_to_approved_ai(



            document_text



        )







    elif decision == "SANITIZE_AND_SEND":



        sanitized_text = mask_sensitive_data(



            document_text,



            image_findings



        )







        ai_response = await send_to_approved_ai(



            sanitized_text



        )
    elif decision == "HITL":

        await save_pending_hitl(
            session_id,
            {
                "text": document_text,
                "findings": image_findings
            }
        )

        ai_response = None

    elif decision == "BLOCK":

        ai_response = None







    current_turn = {



        "timestamp": int(time.time()),



        "isolated_risk": risk_result[



            "isolated_risk"



        ],



        "findings": [



            {



                "type": finding.get("type"),



                "confidence": finding.get(



                    "confidence",



                    1.0



                )



            }



            for finding in image_findings



        ]



    }







    history.append(current_turn)







    await save_history(



        session_id,



        history



    )







    return {



        "session_id": session_id,



        "input_type": "IMAGE",



        "file_name": image_result[



            "file_name"



        ],



        "image_format": image_result[



            "image_format"



        ],



        "width": image_result[



            "width"



        ],



        "height": image_result[



            "height"



        ],



        "ocr_used": image_result[



            "ocr_used"



        ],



        "ocr_engine": image_result[



            "ocr_engine"



        ],



        "extracted_text": document_text,



        "source_segments": source_segments,



        "findings": image_findings,



        "risk": risk_result,



        "policy": policy_result,



        "sanitized_text": sanitized_text,



        "ai_response": ai_response,



        "history_turns": len(history),



        "processing_message": "Image processed successfully."



    }