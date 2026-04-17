import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000';

/* ================= CHAT ================= */

export const postChat = createAsyncThunk(
  "interaction/postChat",
  async (message) => {

    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message })
    });

    return await res.json();
  }
);

/* ================= SAVE ================= */

export const logInteraction = createAsyncThunk(
  "interaction/log",
  async (payload) => {

    const res = await axios.post(
      `${API_BASE}/log-interaction`,
      payload
    );

    alert("✅ Interaction Logged Successfully!");
    return res.data;
  }
);

/* ================= INSIGHTS ================= */

export const fetchInsights = createAsyncThunk(
  "interaction/fetchInsights",
  async () => {
    const res = await axios.get(`${API_BASE}/insights`);
    return res.data;
  }
);

/* ================= SLICE ================= */

const interactionSlice = createSlice({
  name: "interaction",

  initialState: {
    formData: {
      hcpName: "",
      type: "Meeting",
      date: "",
      time: "",
      topics: "",
      materials: [],
      samples: [],
      outcome: "Neutral",
      followUp: ""
    },

    chatHistory: [
      {
        role: "assistant",
        content:
          "Describe the interaction and I will fill the form automatically."
      }
    ],

    insights: { total: 0 }
  },

  /* ================= REDUCERS ================= */

  reducers: {

    updateField: (state, action) => {
      const { field, value } = action.payload;
      state.formData[field] = value;
    },

    addListItem: (state, action) => {
      const { list, item } = action.payload;
      state.formData[list].push(item);
    },

    // ✅ USER MESSAGE ADDED HERE
    addUserMessage: (state, action) => {
      state.chatHistory.push({
        role: "user",
        content: action.payload
      });
    }
  },

  /* ================= EXTRA REDUCERS ================= */

  extraReducers: (builder) => {
    builder

      /* ===== CHAT RESPONSE ===== */
      .addCase(postChat.fulfilled, (state, action) => {

        // assistant reply
        state.chatHistory.push({
          role: "assistant",
          content: action.payload.response
        });

        const data = action.payload.extracted_data;
        if (!data) return;

        // 🔥 AUTO FORM FILL
        if (data.hcp_name)
          state.formData.hcpName = data.hcp_name;

        if (data.interaction_type)
          state.formData.type = data.interaction_type;

        if (data.topics)
          state.formData.topics = data.topics;

        if (data.date)
          state.formData.date = data.date;

        if (data.outcome)
          state.formData.outcome = data.outcome;

        if (data.follow_up)
          state.formData.followUp = data.follow_up;
      })

      /* ===== INSIGHTS ===== */
      .addCase(fetchInsights.fulfilled, (state, action) => {
        state.insights = action.payload;
      });
  }
});

/* ================= EXPORTS ================= */

export const {
  updateField,
  addListItem,
  addUserMessage
} = interactionSlice.actions;

export default interactionSlice.reducer;