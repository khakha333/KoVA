# aws cloud9
import json  # JSON 파싱
import boto3
import streamlit as st

bedrock_runtime = boto3.client(service_name="bedrock-runtime", region_name="us-east-1")

selected_language = 'English'
# 사이드바 언어 선택
selected_language = st.sidebar.selectbox("언어를 선택하세요", ['Korean', 'English'])
st.title("Republic of Korea Visa AI Assistant")

# 사이드바 버튼 생성
if st.sidebar.button("언어 변경"):
    if selected_language == 'English':
        st.session_state.messages = [
            {"role": "system", "content": "Welcome to Republic of Korea Visa AI Assistant! what is the purpose of applying for a visa? Please explain whether you have family or a spouse in Korea, or if you want to find a job, study at a school, etc."}
        ]
        st.session_state.page_title = "Republic of Korea Visa AI Assistant"
    elif selected_language == 'Korean':

        st.session_state.messages = [
            {"role": "system", "content": "한국 비자 조언 AI에 오신 것을 환영합니다! 어떤 목적으로 비자를 받으려고 하십니까? 어떤 상황인지 설명해주세요!"}
        ]
        st.session_state.page_title = "환영합니다"
    st.session_state.history_pairs = []
    
    # 페이지 새로고침
    st.markdown(
        """
        <script>
        window.location.reload();
        </script>
        """,
        unsafe_allow_html=True,
    )
    # if selected_language == 'English':
    #     st.title("Republic of Korea Visa AI Assistant")
    # elif selected_language == 'Korean':
    #     st.title("환영합니다")

st.caption("Powered by Bedrock")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "Welcome to Republic of Korea Visa AI Assistant! what is the purpose of applying for a visa? Please explain whether you have family or a spouse in Korea, or if you want to find a job, study at a school, etc."}
    ]

if 'key' not in st.session_state:
    st.session_state['key'] = 'value'

if "history_pairs" not in st.session_state:
    st.session_state.history_pairs = []

# CSS
st.markdown("""
    <style>
    .chat-container {
        max-width: 800px; 
        margin: 0 auto;
        padding: 10px;
    }
    .user-message, .bot-message {
        margin: 10px 0;
        padding: 10px 15px;
        border-radius: 15px;
        max-width: 70%; 
        display: inline-block;
        word-wrap: break-word;
        word-break: break-word;
    }
    .user-message {
        background-color: #dcf8c6;
        align-self: flex-end;
        text-align: left; 
    }
    .bot-message {
        background-color: #f1f0f0;
        align-self: flex-start;
    }
    .message-box {
        display: flex;
        flex-direction: row;
        align-items: center;
        justify-content: flex-end;
    }
    .message-box.user {
        justify-content: flex-end; 
    }
    .message-box.bot {
        justify-content: flex-start; 
    }
    .profile {
        position: absolute;
        top: 20px;  
        left: -3%;  
        transform: translateX(-50%);  
        max-width: 24px;  
        border-radius: 50%;  
    }
    .message-box.user .profile {
        left: 103%;  
    }
    .message-box.bot .profile {
        left: -3%;  
    }
    </style>
""", unsafe_allow_html=True)

# 지난 메시지 전부 출력
st.write('<div class="chat-container">', unsafe_allow_html=True)
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(
            f'<div class="message-box user">'
            f'<div class="user-message">{message["content"]}</div>'
            f'<img src="https://fonts.gstatic.com/s/i/materialicons/face/v6/24px.svg" class="profile"></div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="message-box bot">'
            f'<img src="https://fonts.gstatic.com/s/i/materialicons/smart_toy/v6/24px.svg" class="profile">'
            f'<div class="bot-message">{message["content"]}</div></div>',
            unsafe_allow_html=True
        )
st.write('</div>', unsafe_allow_html=True)


# 모델로부터 질문에 대한 답변 받는 함수
def get_response(message):
    try:
        # 여기서 메인 프롬프팅
        new_messages = [
            {"role": "user", "content": "Who are you?"},
            {"role": "assistant", "content": "I am a helpful assistant who helps foreigners obtain visas in Korea. Provide the best possible help regarding visa options and processes."},
            {"role": "user", "content": '''
             Here are your specific instructions. Please follow these in all future conversations with the user!
             The user's first request involves situations where they need to obtain a visa in Korea or prepare for a visa in the future for specific purposes such as employment or marriage etc.

             Let's do step by step.
             At the end of each step if anything needs to be improved before moving on to the next section. Before proceeding to the next step, ensure the first one is fully completed. Please don't mention any STEP ; just act on it.
             The output should always summarize the user's situation and ask for the necessary information for the next step.
             In the final step, provide a summary of the user's visa-related details, suggest a tailored solution, and conclude the conversation.
             
             You must answer every question in English. Other languages are not allowed. Please respond in English.
             And don't add overly polite phrases after the questions. Being kind is good, but overly long responses can be uncomfortable.

             ### Step1 ###
                Understand the user about their situation regarding visa issuance.
                Based on the user's situation, determine one of the following three schemas(1. Employment, 2. Study, 3. Marriage), and in the future steps, fill in the information required for that schema.

                The schema is structured as follows:
                - Name (Data Type): Description


                1.Employment
                - stayedOver90Days (boolean): Whether the applicant plans to stay in Korea for more than 90 days
                - continent (string): The continent of the applicant's origin ["Asia", "Europe", "America", "Africa", "Oceania", "Other"]
                - country (string): The applicant's country of origin
                - visaPurpose (string): Purpose of the visa (e.g., "Study", "Employment", "Tourism")
                - intendedJob (string): Desired job in Korea
                - highestEducation (string): The applicant's highest education level (e.g., "High School", "Bachelor's in Korea", "Master's abroad")
                - currentJob (string): The applicant's current job
                - yearsOfExperience (integer): The applicant's total years of experience

                2.Study
                - stayedOver90Days (boolean): Whether the applicant plans to stay in Korea for more than 90 days
                - continent (string): The continent of the applicant's origin ["Asia", "Europe", "America", "Africa", "Oceania", "Other"]
                - country (string): The applicant's country of origin
                - visaPurpose (string): Purpose of the visa (e.g., "Study", "Employment", "Tourism")
                - intendedJob (string): Desired job in Korea
                - highestEducation (string): The applicant's highest education level (e.g., "High School", "Bachelor's in Korea", "Master's abroad")
                - currentJob (string): The applicant's current job
                - yearsOfExperience (integer): The applicant's total years of experience

                3.Marriage
                - spouseGender (string): Gender of the spouse


                Never give some choices about country for user. If you need country information, Just ask by simple sentence.
            
               The output will briefly summarize the user's situation and proceed to gather the necessary information for the selected schema in the next steps.
                If the chosen schema is 1. Employment or 2. Study, the first question will confirm whether the user intends to stay in Korea for more than 90 days.

                Here is an example output:
                {
                    You are from Kazakhstan and wish to stay in Korea for work. Is it correct that you intend to stay in Korea for more than 90 days?
                }
            
             ### Step2 ###
                If the schema is 1. Employment or 2. Study, check if the applicant wants to stay in Korea for more than 90 days.
                Additionally, if the user's country of origin is unknown, ask about their continent and country.

                The output should briefly summarize the user's situation and ask the necessary questions for the next step.
             
             ### Step3 ###
                Confirm what kind of job (profession) the user wants to pursue in Korea.

                The output should briefly summarize the user's situation and ask the next relevant question.
                
             ### Step4 ###
                Confirm the user's education and work experience (to determine their highest level of education.)
                The output should validate their responses and categorize their education and experience accurately.
                
                If the user's work experience is less than one year, skip Step 5 and proceed to Step 5-1.

                Here is an example output:
                {
                    So, you are a software developer with a bachelor's degree and one year of work experience, correct?
                }
             If the user confirms with "Yes" or similar, proceed to the next step.
            
             ### Step5 ###
                Now, based on our previous conversation and the information filled into the schema, please select the most suitable visa and propose it.
                Additionally, provide detailed information about the related requirements, preparation steps, and the visa application process.

                Finally, ask the user if they believe this visa aligns with their situation.
             
             ### Step6 (Final Step) ###
                Finally, Summarize the user's situation and the selected visa information, then ask the user to make a final decision. Based on their decision, provide relevant website links for further reference and application.
                Conclude the conversation.
                (This is the final step. NEVER move to the next step.)

             ### Step5-1 ###
                If the user's work experience is less than one year, Review the response again and clarify the exact educational background and work experience.
                You should express clearly that user CANNOT meet the requirements for the E-7-1 visa due to insufficient work experience.

                If the work experience is indeed less than one year, proceed to Step 5-2.
             
             ### Step5-2 ###
                Explain the current situation and why obtaining the visa is challenging for the user.
                Introduce additional measures to meet the requirements.
                If the user requests more information, proceed to Step 5-3.
             
                Here is an example output:
                {
                    If you hold a bachelor's degree in computer science and have more than one year of relevant work experience, you may qualify for an E-7-1 visa. However, since you currently do not meet the requirement of at least one year of experience, it is challenging to satisfy the employment visa requirements in Korea at this time.
                    Instead, let me introduce alternative ways to meet these requirements:
                    
                    To qualify for an E-7-1 visa, you need to satisfy one of the following conditions:
                    - A master's degree or higher in a relevant field.
                    - A bachelor's degree in a relevant field with at least one year of experience.
                    - At least five years of experience in a relevant field.
                    
                    To obtain an employment visa in Korea, you could consider the following options:
                    - Pursuing a master's degree in a relevant field.
                    - Gaining additional experience of at least one year in the relevant field.
                    
                    These steps can help you meet the eligibility requirements for the E-7-1 visa. Let me know if you need further assistance!
                }
             ### Step5-3 ###
                If the user requests additional information, provide the details and ask if they need further assistance.
                The user may want to know what immediate steps to take. Recommend a different type of visa and suggest activities to prepare for it.
                After responding, proceed to the final step, Step 5-4.

                 Here is an example output:
                    {
                        If you want to start activities in Korea immediately, you can first enter Korea with a student visa instead of a work visa and gain experience locally. Are you interested in learning more about this?
                    }
             ### Step5-4 (Final Step) ###
                Summarize the user's situation, provide suitable visa information, and suggest relevant activities. Then, ask the user to make a final decision. Based on the user's decision, either provide additional information, share links to related websites for visa applications, or share links to websites for related activities.
                Conclude the conversation.
                (This is the final step. NEVER move to the next step.)
                 
             '''},
            {"role": "assistant", "content": "Okay!! Let's start with the first step. Please provide me with the information you need help with."},
            ]
            # 둘 다 text 형태로 삽입하기
        
        for user_text, assistant_text in st.session_state.history_pairs:
            new_messages.append({"role": "user", "content": user_text})
            new_messages.append({"role": "assistant", "content": assistant_text})

        # 이번 사용자 입력 추가
        new_messages.append({"role": "user", "content": message})

        anthropic_messages = []
        for m in new_messages:
            anthropic_messages.append({
                "role": m["role"],
                "content": [{"type": "text", "text": m["content"]}]
            })
            
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": anthropic_messages,
        })


        response = bedrock_runtime.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            body=body,
        )
        response_body = json.loads(response.get("body").read())
        output_text = response_body["content"][0]["text"]

        new_messages.append({"role": "assistant", "content": output_text})
        
        return output_text
    except Exception as e:
        print(e)
        return "Error: " + str(e)


# 채팅 입력받기
if prompt := st.chat_input("Ask What You Want To Know"):
    # 사용자 메시지를 세션 상태에 추가
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(
        f'<div class="message-box user">'
        f'<div class="user-message">{prompt}</div>'
        f'<img src="https://fonts.gstatic.com/s/i/materialicons/face/v6/24px.svg" class="profile"></div>',
        unsafe_allow_html=True
    )

    # 모델 응답 생성
    with st.spinner("Loading Response. Please Wait..."):
        output_text = get_response(prompt)
        
        # assistant 메시지 추가
        st.session_state.messages.append({"role": "assistant", "content": output_text})
        # history_pairs에도 (질문, 답변) 쌍 추가
        st.session_state.history_pairs.append((prompt, output_text))

    # 봇 메시지 출력
    st.markdown(
        f'<div class="message-box bot">'
        f'<img src="https://fonts.gstatic.com/s/i/materialicons/smart_toy/v6/24px.svg" class="profile">'
        f'<div class="bot-message">{output_text}</div></div>',
        unsafe_allow_html=True
    )

