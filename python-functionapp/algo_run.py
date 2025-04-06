import os
import sys
import subprocess
from datetime import datetime
import logging

def setup_logging():
    # For Azure Functions, logging to stdout is preferred
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def extract_output_between_markers(output):
    try:
        lines = output.splitlines()
        start_collecting = False
        collected_lines = []
        for line in lines:
            if '----- Trade Signals -----' in line:
                start_collecting = True
                continue
            elif '----- End of Trade Signals -----' in line:
                break
            elif start_collecting:
                parts = line.split(' - ', 2)
                if len(parts) == 3:
                    content = parts[2].strip()
                else:
                    content = line.strip()
                collected_lines.append(content)
        if collected_lines:
            return '\n'.join(collected_lines).strip()
        else:
            return "No output between markers."
    except Exception as e:
        logging.error(f"Error extracting output between markers: {e}")
        return "Error extracting output."

def run_script_and_capture_output(python_interpreter, script_path, script_name):
    logging.info(f"Attempting to run {script_name} at path: {script_path}")
    try:
        result = subprocess.run(
            [python_interpreter, script_path],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        logging.info(f"{script_name} completed successfully.")
        script_output = result.stdout
        script_base_name = os.path.basename(script_path)
        logging.debug(f"Script base name: {script_base_name}")
        logging.debug(f"Raw output:\n{script_output}")
        
        # Extract output between markers if available, otherwise return all output
        if "----- Trade Signals -----" in script_output:
            captured_output = extract_output_between_markers(script_output)
            logging.info(f"Extracted output between markers: {captured_output}")
            return captured_output
        else:
            return script_output

    except subprocess.CalledProcessError as e:
        logging.error(f"{script_name} failed with return code {e.returncode}")
        logging.error(f"Error output: {e.stdout}")
        return f"ERROR: {script_name} failed with return code {e.returncode}"
    except Exception as e:
        logging.exception(f"Exception occurred while running {script_name}: {e}")
        return f"ERROR: {script_name} failed with exception: {str(e)}"

def main(mytimer=None):
    setup_logging()
    logging.info("Starting automation script.")
    
    if mytimer:
        logging.info(f"Timer trigger executed at: {datetime.now()}")
        logging.info(f"Timer past due: {mytimer.past_due}")

    # List of scripts to run (adjusted to focus on clear_cache.py)
    scripts = [
        "shared/clear_cache.py",
        "shared/update_cache.py",
        "calculations/calculations.py"
    ]

    # Use SCRIPTS_BASE_PATH if provided; otherwise, default to the current working directory
    scripts_base_path = os.getenv('SCRIPTS_BASE_PATH') or os.getcwd()
    python_interpreter = sys.executable
    logging.info(f"Using Python interpreter: {python_interpreter}")
    logging.info(f"Scripts base path: {scripts_base_path}")

    # Execute each script and log its output
    for script in scripts:
        script_path = os.path.join(scripts_base_path, script)
        if not os.path.isfile(script_path):
            logging.error(f"Script '{script}' not found at '{script_path}'. Skipping.")
            continue
            
        logging.info(f"Running {script} now...")
        script_output = run_script_and_capture_output(python_interpreter, script_path, script)
        
        if script_output:
            logging.info(f"Output from {script}:\n{script_output}")
        else:
            logging.info(f"No output captured from {script}")
            
        logging.info(f"Finished running {script}.")
    
    logging.info("All scripts completed.")

if __name__ == "__main__":
    main()