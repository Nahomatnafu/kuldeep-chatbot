For this part of the project, each team member created their own branch to experiment with building a test chatbot. We worked through the full RAG pipeline: ingestion, chunking, retrieval, and response generation to better understand how Retrieval-Augmented Generation works.

During testing, we used different types of documents. Dilasha and Nahom tested the chatbot using an AI-generated music research paper, while Jake tested it using a Statement of Purpose (SOP) document. This allowed us to evaluate how the system handled different writing styles and types of content.

We focused on testing and validating how accurately the chatbot retrieved information from the documents. Currently, the system does not store conversation memory, so each response is generated independently.

Here are some observations from each version:

Nahom and Jake completed their RAG chatbots first. Both had an option to upload a document and ask questions about it. In Jake’s version, the document had to be uploaded each time before asking questions. In Nahom’s version, the document was already embedded in the codebase, so the chatbot answered questions from that fixed document. Dilasha’s version used a Chroma database, where uploaded documents were stored after ingestion, so they did not need to be re-uploaded each time.

All three versions generated accurate answers. Nahom’s chatbot responded the fastest, followed by Jake’s, while Dilasha’s took slightly more time due to the additional database processing.

Dilasha’s chatbot also included a sidebar that displayed uploaded documents. Users could scroll through the list to check if a document existed and had the option to delete documents if needed.

One improvement Dilasha made after testing Jake’s version was related to references. She noticed that Jake’s chatbot sometimes referenced knowledge not provided in the uploaded document. To improve this, her version only generates references if the information is actually retrieved from the document. When a reference is shown, it includes the page number, and clicking on it opens the document directly to that page for verification.

We also tried to upload a 156-page document, and it took around the same amount of time to load the document, and it answered the question pretty fast.
