"""
Fine-tune the base Qwen model on the Q&A dataset using LoRA (or QLoRA).

LoRA:  fine-tunes a small number of extra parameters, keeping the base Qwen
       model mostly frozen. Cheap and fast.
QLoRA: same idea as LoRA, but the base model is loaded in 4-bit (quantized)
       first, so it needs much less GPU memory. Use this when GPU memory is limited.

Fine-tuning teaches the model HOW to respond (style, tone, Egyptian Arabic).
It is NOT the source of facts — that is RAG's job (03_rag_pipeline/).
"""
import os

BASE_MODEL = os.getenv("BASE_MODEL", "Qwen/Qwen2.5-7B-Instruct")
DATASET_PATH = "../02_data/02_qa_pairs/qa_dataset.jsonl"
OUTPUT_DIR = "../finetuned_checkpoints"


def train_lora(use_qlora: bool = False) -> None:
    from datasets import load_dataset
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
    from peft import LoraConfig, get_peft_model

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

    if use_qlora:
        from transformers import BitsAndBytesConfig
        quant_config = BitsAndBytesConfig(load_in_4bit=True)
        model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, quantization_config=quant_config)
    else:
        model = AutoModelForCausalLM.from_pretrained(BASE_MODEL)

    lora_config = LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05, task_type="CAUSAL_LM")
    model = get_peft_model(model, lora_config)

    dataset = load_dataset("json", data_files=DATASET_PATH, split="train")

    def tokenize(example):
        text = f"سؤال: {example['instruction']}\nإجابة: {example['response']}"
        return tokenizer(text, truncation=True, padding="max_length", max_length=256)

    tokenized_dataset = dataset.map(tokenize)

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=3,
        per_device_train_batch_size=2,
        logging_steps=10,
        save_strategy="epoch",
    )

    trainer = Trainer(model=model, args=training_args, train_dataset=tokenized_dataset)
    trainer.train()
    model.save_pretrained(OUTPUT_DIR)


if __name__ == "__main__":
    train_lora(use_qlora=True)  # switch to False if you have enough GPU memory for plain LoRA
