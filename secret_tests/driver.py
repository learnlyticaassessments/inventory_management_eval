import importlib.util
import datetime
import os
import random
import string
import inspect

def test_student_code(solution_path):
    report_dir = os.path.join(os.path.dirname(__file__), "..", "student_workspace")
    report_path = os.path.join(report_dir, "report.txt")
    os.makedirs(report_dir, exist_ok=True)

    spec = importlib.util.spec_from_file_location("student_module", solution_path)
    student_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(student_module)

    IMS = student_module.InventoryManagementSystem

    report_lines = [f"\n=== Inventory Management Test Run at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ==="]

    # Define test cases
    visible_cases = [
        {"desc": "Add item", "func": "add_item", "input": ("Laptop", 10), "expected": {"Laptop": 10}},
        {"desc": "Update stock", "func": "update_stock", "input": ("Laptop", 15), "expected": {"Laptop": 15}},
        {"desc": "Get item stock", "func": "get_item_stock", "input": ("Laptop",), "expected": 15}
    ]

    hidden_cases = [
        {"desc": "Get available items (some zero)", "func": "get_available_items", "input": (), "expected": ["Laptop"]},
        {
            "desc": "Add item multiple times and verify cumulative quantity",
            "func": "add_item",
            "setup": [("add_item", ("Tablet", 3))],
            "input": ("Tablet", 5),
            "expected": {"Tablet": 8}
        }
    ]

    keyword_checks = {
        "add_item": ["+=", "return", "in"],
        "update_stock": ["return", "if", "not"],
        "get_item_stock": ["return", "if", "not"],
        "get_available_items": ["for", "if"]
    }

    randomized_failures = set()

    # Randomized logic check
    try:
        ims_random = IMS()
        rand_item = ''.join(random.choices(string.ascii_lowercase, k=6))
        rand_qty = random.randint(10, 20)

        ims_random.add_item(rand_item, rand_qty)
        if ims_random.get_item_stock(rand_item) != rand_qty:
            randomized_failures.update(["add_item", "get_item_stock"])

        rand_update = random.randint(25, 35)
        ims_random.update_stock(rand_item, rand_update)
        if ims_random.get_item_stock(rand_item) != rand_update:
            randomized_failures.add("update_stock")

        avail = ims_random.get_available_items()
        if rand_item not in avail:
            randomized_failures.add("get_available_items")
    except:
        randomized_failures.update(["add_item", "update_stock", "get_item_stock", "get_available_items"])

    def evaluate_cases(section, cases):
        for i, case in enumerate(cases, 1):
            try:
                ims = IMS()

                # Special setup for all tests EXCEPT "Add item"
                if case["desc"] != "Add item":
                    ims.add_item("Laptop", 10)
                    ims.add_item("Mouse", 0)
                    ims.update_stock("Laptop", 15)

                # Extra setup if defined inside test
                if "setup" in case:
                    for setup_func, setup_args in case["setup"]:
                        getattr(ims, setup_func)(*setup_args)

                method = getattr(ims, case["func"])
                src = inspect.getsource(getattr(IMS, case["func"])).lower()
                reason = None

                if "pass" in src and len(src.strip()) < 80:
                    reason = "Function contains only 'pass'"
                elif str(case["expected"]).replace(" ", "").lower() in src.replace(" ", "").lower() and len(src) < 150:
                    reason = "Hardcoded return detected"
                elif not any(k in src for k in keyword_checks.get(case["func"], [])):
                    reason = f"Missing logic: expected keywords {keyword_checks.get(case['func'])}"

                if case["func"] in randomized_failures:
                    reason = f"Randomized test failed for {case['func']}"

                result = method(*case["input"])

                if isinstance(case["expected"], list):
                    passed = sorted(result) == sorted(case["expected"])
                else:
                    passed = result == case["expected"]

                if reason and not passed:
                    msg = f"❌ {section} Test Case {i} Failed: {case['desc']} | Reason: {reason}"
                elif reason:
                    msg = f"❌ {section} Test Case {i} Failed due to randomized logic failure for {case['func']}"
                    passed = False
                elif not passed:
                    msg = f"❌ {section} Test Case {i} Failed: {case['desc']} | Reason: Output mismatch"
                else:
                    msg = f"✅ {section} Test Case {i} Passed: {case['desc']}"

                print(msg)
                report_lines.append(msg)

            except Exception as e:
                msg = f"❌ {section} Test Case {i} Crashed: {case['desc']} | Error: {str(e)}"
                print(msg)
                report_lines.append(msg)

    evaluate_cases("Visible", visible_cases)
    evaluate_cases("Hidden", hidden_cases)

    with open(report_path, "a", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")


