# 🃏 MTG Commander Recommendation System

An AI-powered Magic: The Gathering Commander deck building assistant that provides intelligent creature recommendations based on machine learning analysis of EDHREC data.

## ✨ Features

- **Smart Recommendations**: ML-powered suggestions using TF-IDF text analysis and pattern recognition
- **Color Identity Validation**: Ensures all recommendations follow MTG color rules
- **Pattern Recognition**: Analyzes keyword synergies, creature types, and power/toughness patterns
- **Price Filtering**: Filter recommendations by card price
- **Interactive Web App**: Clean, modern Streamlit interface
- **Data Scraping**: EDHREC scraper for gathering training data

## 🚀 Live Demo

[Deploy to Streamlit Community Cloud](https://streamlit.io) - *coming soon*

## 📸 Screenshots

*Add screenshots of your app here*

## 🛠️ Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/mtg-commander-recommendations.git
cd mtg-commander-recommendations
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Download NLTK data**
```python
import nltk
nltk.download('stopwords')
nltk.download('punkt')
```

## 📊 Data Setup

The system requires processed MTG card data. You can either:

### Option A: Use the data scraper
```bash
# Run the EDHREC scraper (be respectful of rate limits)
jupyter notebook 00_edhrec_scraper.ipynb
```

### Option B: Use sample data
Place your CSV files in the `data/raw/` directory:
- `all_creatures_clean.csv` - All MTG creatures
- `edhrec_complete_from_slugs.csv` - EDHREC recommendation data

## 🚀 Usage

### Run the Web App
```bash
streamlit run mtg_commander_app.py
```

### Use the Recommendation System Programmatically
```python
from mtg_recommendation_system import create_recommendation_system

# Load the system
system = create_recommendation_system()

# Get recommendations
recommendations = system.get_recommendations("The Ur-Dragon", top_k=20)

for rec in recommendations[:5]:
    print(f"{rec['creature_name']}: {rec['final_score']:.3f}")
```

## 📁 Project Structure

```
mtg-commander-recommendations/
├── data/
│   ├── raw/                    # Raw CSV data files
│   └── processed/              # Processed features and models
├── notebooks/                  # Jupyter notebooks for analysis
│   ├── 00_edhrec_scraper.ipynb
│   ├── 01_initial_setup.ipynb
│   ├── 02_data_exploration.ipynb
│   └── 03_preprocessing.ipynb
├── mtg_recommendation_system.py # Core ML recommendation engine
├── mtg_commander_app.py        # Streamlit web application
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🧠 How It Works

1. **Data Collection**: Scrapes EDHREC for commander/creature recommendation pairs
2. **Text Processing**: Uses TF-IDF to vectorize card oracle text
3. **Pattern Analysis**: Identifies consensus keywords, creature types, and P/T patterns
4. **Similarity Scoring**: Combines text similarity with pattern boosts
5. **Recommendation**: Returns ranked suggestions with detailed scoring

## ⚙️ Configuration

The system supports customizable scoring parameters:

```python
system = create_recommendation_system(
    keyword_boost=0.1,      # Boost for keyword matches
    type_boost=0.1,         # Boost for creature type matches  
    power_boost=0.05,       # Boost for power pattern matches
    toughness_boost=0.05,   # Boost for toughness pattern matches
    known_penalty=0.85,     # Penalty for known recommendations
    short_text_penalty=0.90 # Penalty for cards with short text
)
```

## 📈 Performance

- **Training Data**: ~83,000 commander/creature pairs
- **Recommendation Speed**: ~100ms per commander
- **Accuracy**: Optimized for discovering hidden synergies
- **Coverage**: 1,900+ commanders, 15,000+ creatures

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **EDHREC** for providing the foundational recommendation data
- **Scryfall** for the comprehensive MTG card database and API
- **Wizards of the Coast** for creating Magic: The Gathering

## ⚠️ Disclaimer

This project is unofficial and not affiliated with Wizards of the Coast. Magic: The Gathering is a trademark of Wizards of the Coast LLC.

## 📬 Contact

Your Name - your.email@example.com

Project Link: https://github.com/yourusername/mtg-commander-recommendations