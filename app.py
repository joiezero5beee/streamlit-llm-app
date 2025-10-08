
from dotenv import load_dotenv
load_dotenv()  # カレントの .env を読む

import os
import streamlit as st
# ▼ 変更: 旧 from langchain.llms import OpenAI を撤去し、ChatOpenAI を使用
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# ▼ 追加:
from openai import OpenAI

api_key  = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
base_url = st.secrets.get("OPENAI_BASE_URL") or os.getenv("OPENAI_BASE_URL")  # 使っている場合だけ

if not api_key:
    st.error("OPENAI_API_KEY が見つかりません")
    st.stop()

# 辞書を丸ごと渡さず、使う項目だけを明示
if base_url:
    client = OpenAI(api_key=api_key, base_url=base_url)
else:
    client = OpenAI(api_key=api_key)

# ページ設定
st.set_page_config(
    page_title="AIレシピアドバイザー",
    page_icon="🍳",
    layout="wide"
)

# タイトルと概要
st.title("🍳 AIレシピアドバイザー")
st.markdown("""
### アプリ概要
冷蔵庫にある食材を入力すると、選んだ料理の専門家がそれぞれの視点でレシピを提案します。

### 操作方法
1. 下記から専門家を選択してください
2. 冷蔵庫にある食材を入力してください
3. 「レシピを提案してもらう」ボタンをクリックしてください

専門家の特徴：
- **栄養士（健康重視）**: 栄養バランスと健康面を重視したレシピを提案
- **料理研究家（手軽さ重視）**: 簡単で手軽に作れるレシピを提案  
- **プロシェフ（味重視）**: 本格的で美味しさを追求したレシピを提案
""")

st.divider()

def get_recipe_advice(ingredients: str, expert_type: str) -> str:
    """
    食材と専門家タイプを受け取り、LLMからレシピアドバイスを取得する関数
    
    Args:
        ingredients (str): 入力された食材
        expert_type (str): 選択された専門家タイプ
        
    Returns:
        str: LLMからの回答
    """
    try:
        # OpenAI APIキーの確認（既に必須コードで検証済みだが念のため）
        if not api_key:
            return "エラー: OpenAI APIキーが設定されていません。環境変数OPENAI_API_KEYを設定してください。"
        
        # ▼ 変更: 旧 langchain.llms.OpenAI ではなく ChatOpenAI を利用
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=1000,
            api_key=api_key,
            base_url=base_url
        )
        
        # 専門家タイプに応じたシステムプロンプトの設定
        system_prompts = {
            "栄養士（健康重視）": """あなたは栄養学の専門知識を持つ栄養士です。
健康面と栄養バランスを最優先に考え、以下の観点でレシピを提案してください：
- 栄養価の高い食材の組み合わせ
- カロリーや塩分の適切な管理
- ビタミン・ミネラルの摂取バランス
- 体に優しい調理法の推奨""",
            
            "料理研究家（手軽さ重視）": """あなたは家庭料理に詳しい料理研究家です。
手軽さと実用性を重視し、以下の観点でレシピを提案してください：
- 短時間で作れる簡単な調理法
- 特別な道具や材料を使わない
- 初心者でも失敗しにくい手順
- 作り置きや時短のコツ""",
            
            "プロシェフ（味重視）": """あなたは一流レストランで経験を積んだプロシェフです。
味の完成度と本格性を重視し、以下の観点でレシピを提案してください：
- 食材の持ち味を最大限に活かす調理法
- 深みのある味付けと香りの演出
- プロならではの技術やコツ
- 見た目も美しい盛り付け"""
        }
        
        # プロンプトテンプレートの作成
        prompt_template = PromptTemplate(
            input_variables=["system_prompt", "ingredients"],
            template="""
{system_prompt}

与えられた食材を使って、あなたの専門分野の視点から最適なレシピを1つ提案してください。

使用可能な食材: {ingredients}

以下の形式で回答してください：
## おすすめレシピ: [料理名]

### 材料（2人分）
- [具体的な分量を含む材料リスト]

### 作り方
1. [手順1]
2. [手順2]
...

### ポイント・コツ
- [あなたの専門分野ならではのアドバイス]

### 栄養・特徴
- [この料理の特徴や栄養面での利点]
"""
        )
        
        # LLMChainの作成と実行
        chain = LLMChain(
            llm=llm,
            prompt=prompt_template
        )
        
        result = chain.run(
            system_prompt=system_prompts[expert_type],
            ingredients=ingredients
        )
        
        return result
        
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

# サイドバーで専門家選択
with st.sidebar:
    st.header("🧑‍🍳 専門家を選択")
    expert_type = st.radio(
        "どの専門家にレシピを提案してもらいますか？",
        ["栄養士（健康重視）", "料理研究家（手軽さ重視）", "プロシェフ（味重視）"]
    )
    
    st.markdown(f"**選択中**: {expert_type}")

# メイン画面
col1, col2 = st.columns([2, 1])

with col1:
    st.header("🥬 食材を入力してください")
    
    # 食材入力フォーム
    ingredients = st.text_area(
        "冷蔵庫にある食材を入力してください（例: 鶏肉、玉ねぎ、トマト、チーズ）",
        height=100,
        placeholder="食材名をカンマ区切りで入力してください"
    )
    
    # レシピ提案ボタン
    if st.button("🍳 レシピを提案してもらう", type="primary", use_container_width=True):
        if ingredients.strip():
            with st.spinner(f"{expert_type}がレシピを考えています..."):
                advice = get_recipe_advice(ingredients, expert_type)
            
            st.success("レシピの提案が完了しました！")
            st.markdown("### 📝 レシピ提案")
            st.markdown(advice)
            
        else:
            st.error("食材を入力してください。")

with col2:
    st.header("📋 使い方のヒント")
    st.markdown("""
    **食材入力のコツ:**
    - 具体的な食材名を入力
    - カンマ区切りで複数入力可能
    - 調味料も入力OK
    
    **例:**
    - 鶏もも肉、玉ねぎ、人参
    - 豚バラ、キャベツ、もやし
    - 卵、ご飯、ネギ、醤油
    """)
    
    st.markdown("---")
    st.markdown("### 🔧 環境設定")
    if os.getenv("OPENAI_API_KEY"):
        st.success("✅ OpenAI APIキーが設定されています")
    else:
        st.error("❌ OpenAI APIキーが設定されていません")
        st.markdown("環境変数 `OPENAI_API_KEY` を設定してください。")

# フッター
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
    🍳 AIレシピアドバイザー | Powered by OpenAI & LangChain
    </div>
    """,
    unsafe_allow_html=True
)
