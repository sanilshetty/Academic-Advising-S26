import os
import json
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from rag_pipeline import get_rag_chain, get_retriever
from dotenv import load_dotenv

load_dotenv()

# Sample Golden Dataset (Placeholder for the 50 profiles)
# In a real scenario, load this from a JSON file.
GOLDEN_DATASET = [
    {
        "question": "I have a 3.2 GPA and got a B in CS 180. Am I eligible for CODO?",
        "ground_truth": "To determine eligibility, we check the requirements. Usually, a 3.0 GPA is required, but specific grades in CS 180 are critical. If the requirement is a B or better, you might be eligible, but check for other constraints."
    },
    {
        "question": "What is the CODO deadline for Spring 2026?",
        "ground_truth": "Deadlines vary by semester. Please refer to the official calendar."
    }
]

def run_evaluation():
    print("Initializing Evaluation...")
    
    chain = get_rag_chain()
    retriever = get_retriever()
    
    questions = []
    ground_truths = []
    contexts = []
    answers = []
    
    print(f"Processing {len(GOLDEN_DATASET)} test cases...")
    
    for item in GOLDEN_DATASET:
        q = item["question"]
        gt = item["ground_truth"]
        
        # Run Pipeline
        # Note: We need to extract the actual retrieved docs for Ragas
        # Since our chain wraps the retrieval, we'll confirm the contexts separately 
        # or reconstruct the chain execution to expose them.
        
        # 1. Retrieve
        docs = retriever.invoke(q)
        retrieved_text = [d.page_content for d in docs]
        
        # 2. Generate
        ans = chain.invoke(q)
        
        questions.append(q)
        ground_truths.append(gt)
        contexts.append(retrieved_text)
        answers.append(ans)
        
    # Prepare Dataset for Ragas
    data_dict = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    }
    
    dataset = Dataset.from_dict(data_dict)
    
    print("Running Ragas Evaluation...")
    # metrics=[faithfulness, answer_relevancy, context_precision, context_recall]
    # Note: context_precision/recall require ground_truth
    
    results = evaluate(
        dataset=dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
        ]
    )
    
    print("\nEvaluation Results:")
    print(results)
    
    # Export to JSON
    output_file = "evaluation_report.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=4) # Ragas results might need conversion to dict if it returns a bespoke object
        # Usually results is a Result object, assume .to_pandas() or dict-like access.
        # For safety in this script:
        f.write(str(results))
        
    print(f"Report saved to {output_file}")

if __name__ == "__main__":
    # Check for API Key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set.")
    else:
        # Check for DB
        if not os.path.exists("data/vectordb"):
             print("Error: Vector DB not found. Run ingest.py first.")
        else:
            run_evaluation()
