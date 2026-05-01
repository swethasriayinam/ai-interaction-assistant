import React, { useState, useRef } from "react";
import { useDispatch, useSelector } from "react-redux";

import {
  updateField,
  logInteraction,
  postChat,
  addUserMessage,
  resetFormData
} from "../store/interactionSlice";

import "./LogInteraction.css";

export default function LogInteraction() {

  const dispatch = useDispatch();

  const formData = useSelector(state => state.interaction.formData);
  const chatHistory = useSelector(state => state.interaction.chatHistory);
  const loading = useSelector(state => state.interaction.loading);

  const [message, setMessage] = useState("");
  const [submitStatus, setSubmitStatus] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef(null);


  
  /* ================= EXTRACT TIME FROM MESSAGE ================= */

  const extractTimeFromMessage = (text) => {
    const timePatterns = [
      /(\d{1,2}):(\d{2})\s*(am|pm|AM|PM)?/,
      /(morning|afternoon|evening|night)/i,
      /(\d{1,2})\s*(am|pm|AM|PM)/,
      /(\d{1,2}):(\d{2})\s*(hours?|hrs?)/
    ];

    for (let pattern of timePatterns) {
      const match = text.match(pattern);
      if (match) {
        return match[0];
      }
    }
    return "";
  };

  const getCurrentTimeString = () => {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, "0");
    const minutes = String(now.getMinutes()).padStart(2, "0");
    return `${hours}:${minutes}`;
  };

  /* ================= SENTIMENT DETECTION ================= */

  const detectSentiment = (text) => {
    const lower = text.toLowerCase();

    if (
      lower.includes("interested") ||
      lower.includes("happy") ||
      lower.includes("good") ||
      lower.includes("positive") ||
      lower.includes("excited") ||
      lower.includes("agreed")
    ) {
      return "positive";
    }

    if (
      lower.includes("not interested") ||
      lower.includes("bad") ||
      lower.includes("negative") ||
      lower.includes("rejected") ||
      lower.includes("angry") ||
      lower.includes("declined")
    ) {
      return "negative";
    }

    return "neutral";
  };

  /* ================= VOICE RECORDING ================= */

  const startVoiceRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      const chunks = [];

      mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunks, { type: "audio/webm" });
        const base64Audio = await blobToBase64(blob);
        
        // Send to backend for transcription/summarization
        dispatch(addUserMessage("🎙️ Voice note captured"));
        dispatch(postChat(base64Audio));
        
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      alert("Microphone access denied. Please enable microphone.");
    }
  };

  const stopVoiceRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const blobToBase64 = (blob) => {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result);
      reader.readAsDataURL(blob);
    });
  };

  /* ================= FORM UPDATE ================= */

  const handleChange = (field, value) => {
    dispatch(updateField({ field, value }));
  };

  /* ================= CHAT SEND ================= */

  const handleSend = async () => {
  if (!message.trim()) return;

  dispatch(addUserMessage(message));

  // ✅ TIME DETECTION
  const detectedTime = extractTimeFromMessage(message);

  let timeToSet = getCurrentTimeString();

  if (detectedTime) {
    const date = new Date(`1970-01-01 ${detectedTime}`);
    if (!isNaN(date)) {
      timeToSet = date.toTimeString().slice(0, 5);
    }
  }

  dispatch(updateField({ field: "time", value: timeToSet }));

  // ✅ SENTIMENT DETECTION
  const sentiment = detectSentiment(message);
  dispatch(updateField({ field: "sentiment", value: sentiment }));

  // ✅ CALL BACKEND (IMPORTANT FIX)
  const res = await dispatch(postChat(message)).unwrap();

  // ✅ AUTO-FILL FORM FROM LLM RESPONSE
  if (res.extracted_data) {
    const data = res.extracted_data;

    if (data.hcp_name) dispatch(updateField({ field: "hcpName", value: data.hcp_name }));
    if (data.interaction_type) dispatch(updateField({ field: "type", value: data.interaction_type }));
    if (data.date) dispatch(updateField({ field: "date", value: data.date }));
    if (data.time) dispatch(updateField({ field: "time", value: data.time }));
    if (data.topics) dispatch(updateField({ field: "topics", value: data.topics }));
    if (data.outcome) dispatch(updateField({ field: "outcome", value: data.outcome }));
  }

  setMessage("");
};
  /* ================= SAVE ================= */

  const handleSubmit = async () => {
    // Validate required fields
    if (!formData.hcpName.trim()) {
      alert("⚠️ Please enter HCP Name");
      return;
    }

    // Prepare payload for backend (map frontend field names to backend)
    const payload = {
      hcp_name: formData.hcpName,
      interaction_type: formData.type,
      date: formData.date,
      time: formData.time,
      attendees: formData.attendees,
      topics: formData.topics,
      materials_shown: formData.materialsShared,
      samples_distributed: formData.samplesDistributed,
      outcome: formData.outcome,
      follow_up: formData.followUp,
      notes: formData.notes
    };

    setSubmitStatus("Logging...");

    try {
      const result = await dispatch(logInteraction(payload)).unwrap();
      setSubmitStatus("✅ Interaction logged successfully!");
      
      // Reset form after successful submission
      setTimeout(() => {
        dispatch(resetFormData());
        setSubmitStatus("");
      }, 2000);

    } catch (error) {
      setSubmitStatus("❌ Error logging interaction: " + error.message);
    }
  };

  return (
    <div className="page">

      {/* ================= LEFT FORM ================= */}
      <div className="leftPanel">

        <h2>Log HCP Interaction</h2>

        <h4>Interaction Details</h4>

        <div className="row">
          <div className="field">
            <label>HCP Name</label>
            <input
              value={formData.hcpName}
              onChange={(e)=>handleChange("hcpName",e.target.value)}
              placeholder="Search or select HCP..."
            />
          </div>

          <div className="field">
            <label>Interaction Type</label>
            <select
              value={formData.type}
              onChange={(e)=>handleChange("type",e.target.value)}
            >
              <option>Meeting</option>
              <option>Call</option>
              <option>Email</option>
            </select>
          </div>
        </div>

        <div className="row">
          <div className="field">
            <label>Date</label>
            <input
              type="date"
              value={formData.date}
              onChange={(e)=>handleChange("date",e.target.value)}
            />
          </div>

          <div className="field">
            <label>Time</label>
            <input
              type="time"
              value={formData.time || ""}
              onChange={(e) => handleChange("time", e.target.value)}
            />
          </div>
        </div>

        <div className="field">
          <label>Attendees</label>
          <input placeholder="Enter names or search..." />
        </div>

        <div className="field">
          <label>Topics Discussed</label>
          <textarea
            rows={4}
            value={formData.topics}
            onChange={(e)=>handleChange("topics",e.target.value)}
            placeholder="Enter key discussion points..."
          />
        </div>

        <h4>Materials Shared / Samples Distributed</h4>

        <div className="fieldWithButton">
          <div>
            <label>Materials Shared</label>
            <textarea
              rows={2}
              value={formData.materialsShared || ""}
              onChange={(e)=>handleChange("materialsShared",e.target.value)}
              placeholder="e.g., Brochures, samples, documents..."
            />
          </div>
          <button className="inlineBtn" title="Search or add materials">🔍Search/Add</button>
        </div>

        <div className="fieldWithButton">
          <div>
            <label>Samples Distributed</label>
            <p className="emptyText">No samples added.</p>
          </div>
          <button className="inlineBtn" title="Add sample">+Add sample</button>
        </div>

        <h4>Observed/Inferred HCP Sentiment</h4>

        <div className="sentimentGroup">
          <label className="radioLabel">
            <input
              type="radio"
              name="sentiment"
              value="positive"
              checked={formData.sentiment === "positive"}
              onChange={(e)=>handleChange("sentiment", e.target.value)}
            />
            😊 Positive
          </label>
          <label className="radioLabel">
            <input
              type="radio"
              name="sentiment"
              value="neutral"
              checked={formData.sentiment === "neutral"}
              onChange={(e)=>handleChange("sentiment", e.target.value)}
            />
            😐 Neutral
          </label>
          <label className="radioLabel">
            <input
              type="radio"
              name="sentiment"
              value="negative"
              checked={formData.sentiment === "negative"}
              onChange={(e)=>handleChange("sentiment", e.target.value)}
            />
            😞 Negative
          </label>
        </div>

        <h4>Outcomes</h4>

        <div className="field">
          <textarea
            rows={3}
            value={formData.outcome || ""}
            onChange={(e)=>handleChange("outcome",e.target.value)}
            placeholder="Key outcomes or agreements..."
          />
        </div>

        <h4>Follow-up Actions</h4>

        <div className="field">
          <input
            value={formData.followUp}
            onChange={(e)=>handleChange("followUp",e.target.value)}
            placeholder="Enter follow-up actions..."
          />
        </div>

        {submitStatus && (
          <div className={`statusMessage ${submitStatus.includes("✅") ? "success" : "error"}`}>
            {submitStatus}
          </div>
        )}

        <button 
          className="saveBtn" 
          onClick={handleSubmit}
          disabled={loading}
        >
          {loading ? "Logging..." : "Log Interaction"}
        </button>

      </div>


      {/* ================= RIGHT AI ASSISTANT ================= */}
      <div className="rightPanel">

        <h3>🤖 AI Assistant</h3>
        <p className="subtitle">
          Log interaction details here via chat
        </p>

        <div className="chatBox">

          {chatHistory.map((msg, i)=>(
            <div
              key={i}
              className={msg.role === "assistant"
                ? "assistantMsg"
                : "userMsg"}
            >
              {msg.content}
            </div>
          ))}

        </div>

        <div className="chatInput">
          <input
            value={message}
            placeholder="Describe Interaction..."
            onChange={(e)=>setMessage(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && handleSend()}
          />

          <button 
            className={`voiceBtn ${isRecording ? "recording" : ""}`}
            onClick={isRecording ? stopVoiceRecording : startVoiceRecording}
            title={isRecording ? "Stop recording" : "Record voice note"}
          >
            {isRecording ? "⏹️" : "🎙️"}
          </button>

          <button onClick={handleSend}>Log</button>
        </div>

      </div>

    </div>
  );
}