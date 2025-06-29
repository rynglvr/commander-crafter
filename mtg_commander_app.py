# MTG Commander Recommendation Web App - Clean and Optimized
# Run with: streamlit run mtg_commander_app.py

import streamlit as st
import pandas as pd
import requests
import asyncio
import httpx
from mtg_recommendation_system import create_recommendation_system
import warnings
warnings.filterwarnings('ignore')

# Configure page
st.set_page_config(
    page_title="MTG Commander Crafter",
    page_icon="🃏",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data(ttl=3600)
def get_card_data(card_name):
    try:
        clean_name = card_name.strip().replace("'", "").replace(",", "").replace("//", "")
        url = f"https://api.scryfall.com/cards/named?exact={clean_name}"
        response = requests.get(url, timeout=8)
        if response.status_code == 200:
            data = response.json()
        elif response.status_code == 404:
            url = f"https://api.scryfall.com/cards/named?fuzzy={clean_name}"
            response = requests.get(url, timeout=8)
            if response.status_code != 200:
                return None
            data = response.json()
        else:
            return None
        return {
            'image_url': (data.get('image_uris', {}).get('large') or 
                         data.get('image_uris', {}).get('normal') or 
                         data.get('image_uris', {}).get('small')),
            'price_usd': data.get('prices', {}).get('usd'),
            'scryfall_url': data.get('scryfall_uri', '')
        }
    except Exception:
        return None

async def fetch_card_async(client, card_name):
    clean_name = card_name.strip().replace("'", "").replace(",", "").replace("//", "")
    url = f"https://api.scryfall.com/cards/named?exact={clean_name}"
    try:
        response = await client.get(url, timeout=8)
        if response.status_code == 404:
            url = f"https://api.scryfall.com/cards/named?fuzzy={clean_name}"
            response = await client.get(url, timeout=8)
        if response.status_code == 200:
            data = response.json()
            return card_name, {
                'image_url': (data.get('image_uris', {}).get('large') or 
                              data.get('image_uris', {}).get('normal') or 
                              data.get('image_uris', {}).get('small')),
                'price_usd': data.get('prices', {}).get('usd'),
                'scryfall_url': data.get('scryfall_uri', '')
            }
    except Exception:
        pass
    return card_name, None

async def get_all_card_data_async(card_names):
    async with httpx.AsyncClient() as client:
        tasks = [fetch_card_async(client, name) for name in card_names]
        results = await asyncio.gather(*tasks)
    return dict(results)

@st.cache_data(ttl=1800)
def get_batch_card_data(card_names):
    return asyncio.run(get_all_card_data_async(card_names))

def display_commander_card(commander_name, commander_info):
    col1, col2 = st.columns([1, 2])
    with col1:
        commander_data = get_card_data(commander_name)
        image_url = (commander_data.get('image_url') if commander_data else None) or "https://via.placeholder.com/400x560/2c3e50/ecf0f1?text=Commander"
        caption_text = f"🎖️ {commander_name}"
        if commander_data and commander_data.get('price_usd'):
            try:
                price = float(commander_data['price_usd'])
                caption_text += f" - ${price:.2f}"
            except:
                pass
        st.image(image_url, caption=caption_text, width=280, use_container_width=False)
    with col2:
        pass

def display_recommendation_card(rec, rank, card_data):
    card_name = rec['creature_name']
    if len(card_name) > 14:
        card_name = card_name[:11] + "..."
    score_percentage = rec['final_score'] * 100
    price_display = "N/A"
    if card_data and card_data.get('price_usd'):
        try:
            price = float(card_data['price_usd'])
            price_display = f"${price:.2f}"
        except:
            price_display = "N/A"
    st.markdown(f"**#{rank}. {card_name}** | {price_display} | {score_percentage:.1f}%")
    image_url = (card_data.get('image_url') if card_data else None) or "https://via.placeholder.com/200x350/2c3e50/ecf0f1?text=MTG"
    st.image(image_url, width=200, use_container_width=False)
    if card_data and card_data.get('scryfall_url'):
        st.markdown(f"[🔗 Scryfall]({card_data['scryfall_url']})")

@st.cache_resource
def load_recommendation_system():
    try:
        return create_recommendation_system(    
            keyword_boost=0.1,
            type_boost=0.1,
            power_boost=0.05,
            toughness_boost=0.05,
            known_penalty=0.85,
            short_text_penalty=0.80), None
    except Exception as e:
        return None, f"❌ Error loading system: {str(e)}"

def main():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, .stApp {
            font-family: 'Inter', sans-serif;
            background: #f4f6fa;
            color: #111;
        }
        .main-header {
            text-align: center;
            font-size: 2.8rem;
            font-weight: 700;
            color: #111;
            margin-bottom: 0.25rem;
        }
        .subtitle {
            text-align: center;
            font-size: 1.1rem;
            color: #333;
            margin-bottom: 2rem;
        }
        .stButton button {
            background: linear-gradient(135deg, #264653, #2a9d8f);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            border-radius: 10px;
            transition: all 0.2s ease-in-out;
        }
        .stButton button:hover {
            transform: scale(1.03);
            box-shadow: 0 3px 8px rgba(0,0,0,0.15);
        }
        div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] > div {
            background-color: #ffffff;
            color: #111;
            border-radius: 14px;
            padding: 1.25rem;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
            margin-bottom: 1.5rem;
            transition: transform 0.2s ease;
            border: 1px solid #e0e0e0;
        }
        div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] > div:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.07);
        }
        img {
            border-radius: 8px !important;
        }
        div[data-testid="stElementToolbar"] {
            display: none !important;
        }
        .footer {
            text-align: center;
            font-size: 0.9rem;
            color: #555;
            margin-top: 3rem;
            padding-bottom: 1rem;
        }
        @media (max-width: 768px) {
            .main-header {
                font-size: 2rem !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 class="main-header">🃏 MTG Commander Crafter</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Get AI-powered creature recommendations you won\'t find anywhere else</p>', unsafe_allow_html=True)

    system, error = load_recommendation_system()
    if error:
        st.error(error)
        return

    if st.sidebar.button("Get Recommendations", type="primary"):
        st.session_state.get_recommendations = True

    st.sidebar.header("⚙️ Configuration")
    commanders = sorted(system.features_df['commander'].unique())
    selected_commander = st.sidebar.selectbox("Select a Commander:", commanders)
    num_recommendations = st.sidebar.slider("Recommendations:", 5, 100, 25, 5)
    max_price = st.sidebar.slider("Max Price ($):", 0.0, 100.0, 100.0, 5.0)

    if st.session_state.get('get_recommendations', False):
        commander_info = system.get_commander_info(selected_commander)
        with st.container():
            display_commander_card(selected_commander, commander_info)

        with st.spinner(f"Generating recommendations for {selected_commander}..."):
            recommendations = system.get_recommendations(
                selected_commander, 
                top_k=num_recommendations,
                include_known=True
            )

            if not recommendations:
                st.warning("No recommendations found. Try adjusting your filters.")
                return

            card_names = [rec['creature_name'] for rec in recommendations[:num_recommendations]]
            all_card_data = get_batch_card_data(card_names)

            if max_price < 100:
                filtered_recs = []
                for rec in recommendations:
                    if len(filtered_recs) >= num_recommendations:
                        break
                    card_data = all_card_data.get(rec['creature_name'])
                    if card_data and card_data.get('price_usd'):
                        try:
                            if float(card_data['price_usd']) <= max_price:
                                filtered_recs.append(rec)
                        except (ValueError, TypeError):
                            filtered_recs.append(rec)
                    else:
                        filtered_recs.append(rec)
                recommendations = filtered_recs

            st.markdown(f"### 🎯 Top {len(recommendations)} Recommendations")
            for i in range(0, len(recommendations), 3):
                cols = st.columns(3, gap="large")
                for j in range(3):
                    if i + j < len(recommendations):
                        rec = recommendations[i + j]
                        card_data = all_card_data.get(rec['creature_name'])
                        rank = i + j + 1
                        with cols[j]:
                            with st.container():
                                display_recommendation_card(rec, rank, card_data)

            if st.button("📅 Export as CSV"):
                df = pd.DataFrame(recommendations)
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    f"{selected_commander.replace(' ', '_')}_recommendations.csv",
                    "text/csv"
                )

    st.markdown("---")
    st.markdown("""
    <div class="footer">
        🃏<br>
        <small>Card data provided by <a href="https://scryfall.com/" target="_blank" style="color: #336;">Scryfall</a></small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
