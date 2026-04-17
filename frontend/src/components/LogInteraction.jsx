import React, { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  updateField,
  logInteraction,
  postChat,
  addUserMessage
} from "../store/interactionSlice";

import "./LogInteraction.css";

export default function LogInteraction() {

  const dispatch = useDispatch();

  const formData = useSelector(state => state.interaction.formData);
  const chatHistory = useSelector(state => state.interaction.chatHistory);

  const [message, setMessage] = useState("");

  /* ================= FORM UPDATE ================= */

  const handleChange = (field, value) => {
    dispatch(updateField({ field, value }));
  };

  /* ================= CHAT SEND ================= */

  const handleSend = () => {
    if (!message.trim()) return;

    dispatch(addUserMessage(message)); // show user message
    dispatch(postChat(message));       // send to AI

    setMessage("");
  };

  /* ================= SAVE ================= */

  const handleSubmit = () => {
    dispatch(logInteraction(formData));
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
            <input type="time"/>
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

        <div className="field">
          <label>Outcome</label>
          <select
            value={formData.outcome}
            onChange={(e)=>handleChange("outcome",e.target.value)}
          >
            <option>Positive</option>
            <option>Neutral</option>
            <option>Negative</option>
          </select>
        </div>

        <div className="field">
          <label>Follow Up</label>
          <input
            value={formData.followUp}
            onChange={(e)=>handleChange("followUp",e.target.value)}
          />
        </div>

        <button className="saveBtn" onClick={handleSubmit}>
          Log Interaction
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
          />

          <button onClick={handleSend}>Log</button>
        </div>

      </div>

    </div>
  );
}