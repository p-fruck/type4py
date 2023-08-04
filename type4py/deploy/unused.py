# Alternative implementation of type_check_json_pred, was commented out originally
# def type_check_json_pred(pre_trained_m: PretrainedType4Py, source_file_path: str):
#     pre_trained_m.load_pretrained_model()
#     src_f_read = read_file(source_file_path)
#     src_f_ext = analyze_src_f(src_f_read).to_dict()
#     logger.info("Extracted type hints and JSON-representation of input source file")

#     logger.info("Predicting type annotations for the given file:")
#     src_f_ext = infer_single_file(src_f_ext, pre_trained_m)


# Never called anywhere
def predict_types_src_code(pre_trained_m: PretrainedType4Py, src_code: str) -> dict:
    src_f_ext = analyze_src_f(src_code).to_dict()
    logger.info("Extracted type hints and JSON-representation of input source file")

    logger.info("Predicting type annotations for the given file:")
    src_f_ext = get_type_preds_single_file(src_f_ext, pre_trained_m)

    return src_f_ext

# This function was never called anywhere
def type_check_json_pred(source_file_path: str, tc_resuls: list):

    src_f_read = read_file(source_file_path)
    src_f_ext = load_json(join(dirname(source_file_path),
                              splitext(basename(source_file_path))[0]+"_type4py_typed.json"))

    tc_resuls.append((source_file_path, type_check_inferred_types(src_f_ext, src_f_read, join(dirname(source_file_path),
                              splitext(basename(source_file_path))[0]+OUTPUT_FILE_SUFFIX))))


# Called in type_check_json_pred
def type_check_inferred_types(src_f_ext: dict, src_f_read: str, src_f_o_path):
    mypy_tc = MypyManager('mypy', 20)
    preds_type_checked: Tuple[bool, PredictionType] = []

    for m_v, m_v_t in src_f_ext['variables'].items():
        # The predictions for module-level vars
        for p, s in src_f_ext['variables_p'][m_v]:
            logger.info(f"Annotating module-level variable {m_v} with {p}")
            src_f_ext['variables'][m_v] = p
            is_tc, p_type = type_check_pred(src_f_read, src_f_o_path, src_f_ext, mypy_tc, p, m_v_t)
            preds_type_checked.append((is_tc, p_type))
            if not is_tc:
                src_f_ext['variables'][m_v] = m_v_t

    for i, fn in enumerate(src_f_ext['funcs']):
        for p_n, p_t in fn['params'].items():
            # The predictions for arguments for module-level functions
            for p, s in fn['params_p'][p_n]:
                logger.info(f"Annotating function parameter {p_n} with {p}")
                src_f_ext['funcs'][i]['params'][p_n] = p
                is_tc, p_type = type_check_pred(src_f_read, src_f_o_path, src_f_ext, mypy_tc, p, p_t)
                preds_type_checked.append((is_tc, p_type))
                if not is_tc:
                    src_f_ext['funcs'][i]['params'][p_n] = p_t

        # The predictions local variables for module-level functions
        for fn_v, fn_v_t in fn['variables'].items():
            for p, s in fn['variables_p'][fn_v]:
                logger.info(f"Annotating function variable {fn_v} with {p}")
                src_f_ext['funcs'][i]['variables'][fn_v] = p
                is_tc, p_type = type_check_pred(src_f_read, src_f_o_path, src_f_ext, mypy_tc, p, fn_v_t)
                preds_type_checked.append((is_tc, p_type))
                if not is_tc:
                    src_f_ext['funcs'][i]['variables'][fn_v] = fn_v_t

        # The return type for module-level functions
        if src_f_ext['funcs'][i]['ret_exprs'] != []:
            org_t = src_f_ext['funcs'][i]['ret_type']
            for p, s in src_f_ext['funcs'][i]['ret_type_p']:
                logger.info(f"Annotating function {src_f_ext['funcs'][i]['name']} return with {p}")
                src_f_ext['funcs'][i]['ret_type'] = p
                is_tc, p_type = type_check_pred(src_f_read, src_f_o_path, src_f_ext, mypy_tc, p, org_t)
                preds_type_checked.append((is_tc, p_type))
                if not is_tc:
                    src_f_ext['funcs'][i]['ret_type'] = org_t

    # The type of class-level vars
    for c_i, c in enumerate(src_f_ext['classes']):
        for c_v, c_v_t in c['variables'].items():
            for p, s in c['variables_p'][c_v]:
                logger.info(f"Annotating class variable {c_v} with {p}")
                src_f_ext['classes'][c_i]['variables'][c_v] = p
                is_tc, p_type = type_check_pred(src_f_read, src_f_o_path, src_f_ext, mypy_tc, p, c_v_t)
                preds_type_checked.append((is_tc, p_type))
                if not is_tc:
                    src_f_ext['classes'][c_i]['variables'][c_v] = c_v_t

        # The type of arguments for class-level functions
        for fn_i, fn in enumerate(c['funcs']):
            for p_n, p_t in fn["params"].items():
                for p, s in fn["params_p"][p_n]:
                    logger.info(f"Annotating function parameter {p_n} with {p}")
                    src_f_ext['classes'][c_i]['funcs'][fn_i]['params'][p_n] = p
                    is_tc, p_type = type_check_pred(src_f_read, src_f_o_path, src_f_ext, mypy_tc, p, p_t)
                    preds_type_checked.append((is_tc, p_type))
                    if not is_tc:
                        src_f_ext['classes'][c_i]['funcs'][fn_i]['params'][p_n] = p_t

            # The type of local variables for class-level functions
            for fn_v, fn_v_t in fn['variables'].items():
                for p, s in fn['variables_p'][fn_v]:
                    logger.info(f"Annotating function variable {fn_v} with {p}")
                    src_f_ext['classes'][c_i]['funcs'][fn_i]['variables'][fn_v] = p
                    is_tc, p_type = type_check_pred(src_f_read, src_f_o_path, src_f_ext, mypy_tc, p, fn_v_t)
                    preds_type_checked.append((is_tc, p_type))
                    if not is_tc:
                        src_f_ext['classes'][c_i]['funcs'][fn_i]['variables'][fn_v] = fn_v_t

            # The return type for class-level functions
            if src_f_ext['classes'][c_i]['funcs'][fn_i]['ret_exprs'] != []:
                org_t = src_f_ext['classes'][c_i]['funcs'][fn_i]['ret_type']
                for p, s in src_f_ext['classes'][c_i]['funcs'][fn_i]['ret_type_p']:
                    logger.info(f"Annotating function {src_f_ext['classes'][c_i]['funcs'][fn_i]['name']} return with {p}")
                    src_f_ext['classes'][c_i]['funcs'][fn_i]['ret_type'] = p
                    is_tc, p_type = type_check_pred(src_f_read, src_f_o_path, src_f_ext, mypy_tc, p, org_t)
                    preds_type_checked.append((is_tc, p_type))
                    if not is_tc:
                        src_f_ext['classes'][c_i]['funcs'][fn_i]['ret_type'] = org_t

    #apply_inferred_types(src_f_read, src_f_ext, src_f_o_path)
    return report_type_check_preds(preds_type_checked)


# Called as the result of unused function type_check_inferred_types
def report_type_check_preds(
    type_check_preds: List[Tuple[bool, PredictionType]]
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    no_p_equal_gt = 0
    no_p_equal_gt_tc = 0
    no_p_not_equal_gt = 0
    no_p_not_equal_gt_tc = 0
    no_p_wo_gt = 0
    no_p_wo_gt_tc = 0

    p_equal_gt = None
    p_not_equal_gt = None
    p_wo_gt = None

    for is_tc, p_t in type_check_preds:
        if p_t == PredictionType.p_equal_gt:
            no_p_equal_gt += 1
            if is_tc:
                no_p_equal_gt_tc += 1
        elif p_t == PredictionType.p_not_equal_gt:
            no_p_not_equal_gt += 1
            if is_tc:
                no_p_not_equal_gt_tc += 1
        elif p_t == PredictionType.p_wo_gt:
            no_p_wo_gt += 1
            if is_tc:
                no_p_wo_gt_tc += 1

    if no_p_equal_gt != 0:
        p_equal_gt = no_p_equal_gt_tc / no_p_equal_gt
        logger.info(f"g -> (p==g) {p_equal_gt:.2f}")
    if no_p_not_equal_gt != 0:
        p_not_equal_gt = no_p_not_equal_gt_tc / no_p_not_equal_gt
        logger.info(f"g -> (p!=g) {p_not_equal_gt:.2f}")
    if no_p_wo_gt != 0:
        p_wo_gt = no_p_wo_gt_tc / no_p_wo_gt
        logger.info(f"e -> p {p_wo_gt:.2f}")

    return p_equal_gt, p_not_equal_gt, p_wo_gt


# was commented out originally. Was originally invoked in infer_main for no reason.
# def get_type_slots_preds_file(source_file_path: str) -> list:
#     src_f_read = read_file(source_file_path)
#     src_f_ext = load_json(join(dirname(source_file_path),
#                               splitext(basename(source_file_path))[0]+"_type4py_typed.json"))

#     f_type_slots_preds = []

#     for m_v, m_v_t in tqdm(src_f_ext['variables'].items()):
#         # The predictions for module-level vars
#         for p, s in src_f_ext['variables_p'][m_v]:
#             src_f_ext['variables'][m_v] = p
#             f_type_slots_preds.append((source_file_path, src_f_read, src_f_ext, ('variables', m_v), m_v_t, p))

#     for i, fn in tqdm(enumerate(src_f_ext['funcs']), total=len(src_f_ext['funcs']), desc="[module][funcs]"):
#         for p_n, p_t in fn['params'].items():
#             # The predictions for arguments for module-level functions
#             for p, s in fn['params_p'][p_n]:
#                 src_f_ext['funcs'][i]['params'][p_n] = p
#                 f_type_slots_preds.append((source_file_path, src_f_read, src_f_ext, ('funcs', i, 'params', p_n), p_t, p))

#         # The predictions local variables for module-level functions
#         for fn_v, fn_v_t in fn['variables'].items():
#             for p, s in fn['variables_p'][fn_v]:
#                 src_f_ext['funcs'][i]['variables'][fn_v] = p
#                 f_type_slots_preds.append((source_file_path, src_f_read, src_f_ext, ('funcs', i, 'variables', fn_v), fn_v_t, p))

#         # The return type for module-level functions
#         if src_f_ext['funcs'][i]['ret_exprs'] != []:
#             org_t = src_f_ext['funcs'][i]['ret_type']
#             for p, s in src_f_ext['funcs'][i]['ret_type_p']:
#                 src_f_ext['funcs'][i]['ret_type'] = p
#                 f_type_slots_preds.append((source_file_path, src_f_read, src_f_ext, ('funcs', i, 'ret_type'), org_t, p))

#     # The type of class-level vars
#     for c_i, c in tqdm(enumerate(src_f_ext['classes']), total=len(src_f_ext['classes']), desc="[module][classes]"):
#         for c_v, c_v_t in c['variables'].items():
#             for p, s in c['variables_p'][c_v]:
#                 src_f_ext['classes'][c_i]['variables'][c_v] = p
#                 f_type_slots_preds.append((source_file_path, src_f_read, src_f_ext, ('classes', c_i, 'variables', c_v), c_v_t, p))

#         # The type of arguments for class-level functions
#         for fn_i, fn in enumerate(c['funcs']):
#             for p_n, p_t in fn["params"].items():
#                 for p, s in fn["params_p"][p_n]:
#                     src_f_ext['classes'][c_i]['funcs'][fn_i]['params'][p_n] = p
#                     f_type_slots_preds.append((source_file_path, src_f_read, src_f_ext, ('classes', c_i, 'funcs', fn_i, 'params', p_n), p_t, p))

#             # The type of local variables for class-level functions
#             for fn_v, fn_v_t in fn['variables'].items():
#                 for p, s in fn['variables_p'][fn_v]:
#                     src_f_ext['classes'][c_i]['funcs'][fn_i]['variables'][fn_v] = p
#                     f_type_slots_preds.append((source_file_path, src_f_read, src_f_ext, ('classes', c_i, 'funcs', fn_i, 'variables', fn_v), fn_v_t, p))

#             # The return type for class-level functions
#             if src_f_ext['classes'][c_i]['funcs'][fn_i]['ret_exprs'] != []:
#                 org_t = src_f_ext['classes'][c_i]['funcs'][fn_i]['ret_type']
#                 for p, s in src_f_ext['classes'][c_i]['funcs'][fn_i]['ret_type_p']:
#                     src_f_ext['classes'][c_i]['funcs'][fn_i]['ret_type'] = p
#                     f_type_slots_preds.append((source_file_path, src_f_read, src_f_ext, ('classes', c_i, 'funcs', fn_i, 'ret_type'), org_t, p))

#     #apply_inferred_types(src_f_read, src_f_ext, src_f_o_path)
#     return f_type_slots_preds
