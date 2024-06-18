# TeamForgeAI/plugins/Ollama_Workbench/main-workbench.py
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json
import time

OLLAMA_URL = "http://localhost:11434/api"

def get_available_models():
    response = requests.get(f"{OLLAMA_URL}/tags")
    response.raise_for_status()
    models = [
        model["name"]
        for model in response.json()["models"]
        if "embed" not in model["name"]
    ]
    return models

def call_ollama(model, prompt=None, image=None, temperature=0.5, max_tokens=150, presence_penalty=0.0, frequency_penalty=0.0, context=None):
    payload = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "presence_penalty": presence_penalty,
        "frequency_penalty": frequency_penalty,
        "context": context if context is not None else [],
    }
    if prompt:
        payload["prompt"] = prompt
    if image:
        files = {"image": image}
        response = requests.post(f"{OLLAMA_URL}/generate", data=payload, files=files, stream=True)
    else:
        response = requests.post(f"{OLLAMA_URL}/generate", json=payload, stream=True)
    try:
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return f"An error occurred: {str(e)}", None
    response_parts = []
    for line in response.iter_lines():
        part = json.loads(line)
        response_parts.append(part.get("response", ""))
        if part.get("done", False):
            break
    return "".join(response_parts), part.get("context", None)

def performance_test(models, prompt, temperature=0.5, max_tokens=150, presence_penalty=0.0, frequency_penalty=0.0, context=None):
    results = {}
    for model in models:
        start_time = time.time()
        result, _ = call_ollama(model, prompt, temperature=temperature, max_tokens=max_tokens, presence_penalty=presence_penalty, frequency_penalty=frequency_penalty, context=context)
        end_time = time.time()
        elapsed_time = end_time - start_time
        results[model] = (result, elapsed_time)
        time.sleep(0.1)
    return results

def vision_test(models, image, temperature=0.5, max_tokens=150, presence_penalty=0.0, frequency_penalty=0.0, context=None):
    results = {}
    for model in models:
        start_time = time.time()
        result, _ = call_ollama(model, image=image, temperature=temperature, max_tokens=max_tokens, presence_penalty=presence_penalty, frequency_penalty=frequency_penalty, context=context)
        end_time = time.time()
        elapsed_time = end_time - start_time
        results[model] = (result, elapsed_time)
        time.sleep(0.1)
    return results

def check_json_handling(model, temperature, max_tokens, presence_penalty, frequency_penalty):
    prompt = "Return the following data in JSON format: name: John, age: 30, city: New York"
    result, _ = call_ollama(model, prompt=prompt, temperature=temperature, max_tokens=max_tokens, presence_penalty=presence_penalty, frequency_penalty=frequency_penalty)
    try:
        json.loads(result)
        return True
    except json.JSONDecodeError:
        return False

def check_function_calling(model, temperature, max_tokens, presence_penalty, frequency_penalty):
    prompt = "Define a function named 'add' that takes two numbers and returns their sum. Then call the function with arguments 5 and 3."
    result, _ = call_ollama(model, prompt=prompt, temperature=temperature, max_tokens=max_tokens, presence_penalty=presence_penalty, frequency_penalty=frequency_penalty)
    return "8" in result

def list_local_models():
    response = requests.get(f"{OLLAMA_URL}/tags")
    response.raise_for_status()
    models = response.json().get("models", [])
    if not models:
        st.write("No local models available.")
        return
    
    # Prepare data for the dataframe
    data = []
    for model in models:
        size_gb = model.get('size', 0) / (1024**3)  # Convert bytes to GB
        modified_at = model.get('modified_at', 'Unknown')
        if modified_at != 'Unknown':
            modified_at = datetime.fromisoformat(modified_at).strftime('%Y-%m-%d %H:%M:%S')
        data.append({
            "Model Name": model['name'],
            "Size (GB)": size_gb,
            "Modified At": modified_at
        })
    
    # Create a pandas dataframe
    df = pd.DataFrame(data)

    # Calculate height based on the number of rows
    row_height = 35  # Set row height
    height = row_height * len(df) + 35  # Calculate height
    
    # Display the dataframe with Streamlit
    st.dataframe(df, use_container_width=True, height=height, hide_index=True)

def pull_model(model_name):
    payload = {"name": model_name, "stream": True}
    response = requests.post(f"{OLLAMA_URL}/pull", json=payload, stream=True)
    response.raise_for_status()
    progress_bar = st.progress(0)
    status_text = st.empty()
    results = []
    total = None
    st.write(f"📥 Pulling model: `{model_name}`")
    for line in response.iter_lines():
        line = line.decode("utf-8")  # Decode the line from bytes to str
        data = json.loads(line)
        
        if "total" in data and "completed" in data:
            total = data["total"]
            completed = data["completed"]
            progress = completed / total
            progress_bar.progress(progress)
            status_text.text(f"Progress: {progress * 100:.2f}%")
        else:
            progress = None
            if not data["status"].startswith("pulling"):
                status_text.text(data["status"])
        
        if data["status"] == "success":
            break
        
    return results

def show_model_info(model_name):
    payload = {"name": model_name}
    response = requests.post(f"{OLLAMA_URL}/show", json=payload)
    response.raise_for_status()
    return response.json()

def remove_model(model_name):
    payload = {"name": model_name}
    response = requests.delete(f"{OLLAMA_URL}/delete", json=payload)
    if response.status_code == 200:
        try:
            return response.json()
        except json.JSONDecodeError:
            return {"status": "success", "message": f"Model '{model_name}' removed successfully."}
    else:
        return {"status": "error", "message": f"Failed to remove model '{model_name}'. Status code: {response.status_code}"}

def model_comparison_test():
    st.header("Model Comparison by Response Quality")
    available_models = get_available_models()
    selected_models = st.multiselect("Select the models you want to compare:", available_models)
    temperature = st.slider("Select the temperature:", min_value=0.0, max_value=1.0, value=0.5)
    max_tokens = st.number_input("Max tokens:", value=150)
    presence_penalty = st.number_input("Presence penalty:", value=0.0)
    frequency_penalty = st.number_input("Frequency penalty:", value=0.0)
    prompt = st.text_area("Enter the prompt:", value="Write a short story about a brave knight.")

    if st.button("Compare Models", key="compare_models"):
        results = performance_test(selected_models, prompt, temperature, max_tokens, presence_penalty, frequency_penalty)
        for model, (result, elapsed_time) in results.items():
            st.subheader(f"Results for {model} (Time taken: {elapsed_time:.2f} seconds):")
            st.write(result)
            st.write("JSON Handling Capability: ", "✅" if check_json_handling(model, temperature, max_tokens, presence_penalty, frequency_penalty) else "❌")
            st.write("Function Calling Capability: ", "✅" if check_function_calling(model, temperature, max_tokens, presence_penalty, frequency_penalty) else "❌")

def contextual_response_test():
    st.header("Contextual Response Test by Model")
    available_models = get_available_models()
    selected_model = st.selectbox("Select the model you want to test:", available_models)
    prompts = st.text_area("Enter the prompts (one per line):", value="Hi, how are you?\nWhat's your name?\nTell me a joke.")
    temperature = st.slider("Select the temperature:", min_value=0.0, max_value=1.0, value=0.5)
    max_tokens = st.number_input("Max tokens:", value=150)
    presence_penalty = st.number_input("Presence penalty:", value=0.0)
    frequency_penalty = st.number_input("Frequency penalty:", value=0.0)

    if st.button("Start Contextual Test", key="start_contextual_test"):
        prompt_list = [p.strip() for p in prompts.split("\n")]
        context = []
        for prompt in prompt_list:
            start_time = time.time()
            result, context = call_ollama(selected_model, prompt=prompt, temperature=temperature, max_tokens=max_tokens, presence_penalty=presence_penalty, frequency_penalty=frequency_penalty, context=context)
            end_time = time.time()
            elapsed_time = end_time - start_time
            st.subheader(f"Prompt: {prompt} (Time taken: {elapsed_time:.2f} seconds)")
            st.write(f"Response: {result}")
        st.write("JSON Handling Capability: ", "✅" if check_json_handling(selected_model, temperature, max_tokens, presence_penalty, frequency_penalty) else "❌")
        st.write("Function Calling Capability: ", "✅" if check_function_calling(selected_model, temperature, max_tokens, presence_penalty, frequency_penalty) else "❌")

def feature_test():
    st.header("Model Feature Test")
    available_models = get_available_models()
    selected_model = st.selectbox("Select the model you want to test:", available_models)
    temperature = st.slider("Select the temperature:", min_value=0.0, max_value=1.0, value=0.5)
    max_tokens = st.number_input("Max tokens:", value=150)
    presence_penalty = st.number_input("Presence penalty:", value=0.0)
    frequency_penalty = st.number_input("Frequency penalty:", value=0.0)

    if st.button("Run Feature Test", key="run_feature_test"):
        json_result = check_json_handling(selected_model, temperature, max_tokens, presence_penalty, frequency_penalty)
        function_result = check_function_calling(selected_model, temperature, max_tokens, presence_penalty, frequency_penalty)

        st.markdown(f"### JSON Handling Capability: {'✅ Success!' if json_result else '❌ Failure!'}")
        st.markdown(f"### Function Calling Capability: {'✅ Success!' if function_result else '❌ Failure!'}")

def vision_comparison_test():
    st.header("Vision Model Comparison")
    available_models = get_available_models()
    selected_models = st.multiselect("Select the models you want to compare:", available_models)
    temperature = st.slider("Select the temperature:", min_value=0.0, max_value=1.0, value=0.5)
    max_tokens = st.number_input("Max tokens:", value=150)
    presence_penalty = st.number_input("Presence penalty:", value=0.0)
    frequency_penalty = st.number_input("Frequency penalty:", value=0.0)
    uploaded_file = st.file_uploader("Choose an image...", type="jpg")

    if st.button("Compare Vision Models", key="compare_vision_models") and uploaded_file is not None:
        results = vision_test(selected_models, uploaded_file, temperature, max_tokens, presence_penalty, frequency_penalty)
        for model, (result, elapsed_time) in results.items():
            st.subheader(f"Results for {model} (Time taken: {elapsed_time:.2f} seconds):")
            st.write(result)

def list_models():
    st.header("List Local Models")
    models = list_local_models()
    if models:
        # Prepare data for the dataframe
        data = []
        for model in models:
            size_gb = model.get('size', 0) / (1024**3)  # Convert bytes to GB
            modified_at = model.get('modified_at', 'Unknown')
            if modified_at != 'Unknown':
                modified_at = datetime.fromisoformat(modified_at).strftime('%Y-%m-%d %H:%M:%S')
            data.append({
                "Model Name": model['name'],
                "Size (GB)": size_gb,
                "Modified At": modified_at
            })
        
        # Create a pandas dataframe
        df = pd.DataFrame(data)

        # Calculate height based on the number of rows
        row_height = 35  # Set row height
        height = row_height * len(df) + 35  # Calculate height
        
        # Display the dataframe with Streamlit
        st.dataframe(df, use_container_width=True, height=height, hide_index=True)

def pull_models():
    st.header("Pull a Model from Ollama Library")
    model_name = st.text_input("Enter the name of the model you want to pull:")
    if st.button("Pull Model", key="pull_model"):
        if model_name:
            result = pull_model(model_name)
            for status in result:
                st.write(status)
        else:
            st.error("Please enter a model name.")

def show_model_details():
    st.header("Show Model Information")
    available_models = get_available_models()
    selected_model = st.selectbox("Select the model you want to show details for:", available_models)
    if st.button("Show Model Information", key="show_model_information"):
        details = show_model_info(selected_model)
        st.json(details)

def remove_model_ui():
    st.header("Remove a Model")
    available_models = get_available_models()
    selected_model = st.selectbox("Select the model you want to remove:", available_models)
    confirm_label = f"❌ Confirm removal of model `{selected_model}`"
    confirm = st.checkbox(confirm_label)
    if st.button("Remove Model", key="remove_model") and confirm:
        if selected_model:
            result = remove_model(selected_model)
            st.write(result["message"])
            # Update the list of available models
            st.session_state.available_models = get_available_models()
            st.experimental_rerun()
        else:
            st.error("Please select a model.")

def main():
    if 'selected_test' not in st.session_state:
        st.session_state.selected_test = None

    with st.sidebar:
        st.markdown(
            '<div style="text-align: left;">'
            '<h1 class="logo" style="font-size: 50px;">🦙 Ollama <span style="color: orange;">Workbench</span></h1>'
            "</div>",
            unsafe_allow_html=True,
        )
        st.subheader("Maintain")
        if st.button("List Local Models", key="button_list_models"):
            st.session_state.selected_test = "List Local Models"
        if st.button("Show Model Information", key="button_show_model_info"):
            st.session_state.selected_test = "Show Model Information"
        if st.button("Pull a Model", key="button_pull_model"):
            st.session_state.selected_test = "Pull a Model"
        if st.button("Remove a Model", key="button_remove_model"):
            st.session_state.selected_test = "Remove a Model"
        
        st.subheader("Test")
        if st.button("Model Feature Test", key="button_feature_test"):
            st.session_state.selected_test = "Model Feature Test"
        if st.button("Model Comparison by Response Quality", key="button_model_comparison"):
            st.session_state.selected_test = "Model Comparison by Response Quality"
        if st.button("Contextual Response Test by Model", key="button_contextual_response"):
            st.session_state.selected_test = "Contextual Response Test by Model"
        if st.button("Vision Model Comparison", key="button_vision_model_comparison"):
            st.session_state.selected_test = "Vision Model Comparison"

    if st.session_state.selected_test == "Model Comparison by Response Quality":
        model_comparison_test()
    elif st.session_state.selected_test == "Contextual Response Test by Model":
        contextual_response_test()
    elif st.session_state.selected_test == "Model Feature Test":
        feature_test()
    elif st.session_state.selected_test == "List Local Models":
        list_models()
    elif st.session_state.selected_test == "Pull a Model":
        pull_models()
    elif st.session_state.selected_test == "Show Model Information":
        show_model_details()
    elif st.session_state.selected_test == "Remove a Model":
        remove_model_ui()
    elif st.session_state.selected_test == "Vision Model Comparison":
        vision_comparison_test()
    else:
        st.write("""
            ### Welcome to the Ollama Workbench!
            Use the sidebar to select a test or maintenance function.

            #### Maintain
            - **List Local Models**: View a list of all locally available models, including their size and last modified date.
            - **Show Model Information**: Display detailed information about a selected model.
            - **Pull a Model**: Download a new model from the Ollama library.
            - **Remove a Model**: Delete a selected model from the local storage.

            #### Test
            - **Model Feature Test**: Test a model's capability to handle JSON and function calls.
            - **Model Comparison by Response Quality**: Compare the response quality of multiple models for a given prompt.
            - **Contextual Response Test by Model**: Test how well a model maintains context across multiple prompts.
            - **Vision Model Comparison**: Compare the performance of vision models using the same test image.
        """)

if __name__ == "__main__":
    main()