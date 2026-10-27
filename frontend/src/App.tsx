import { ChatPanel } from "@/components/pages/ChatPanel";
import { LocaleProvider } from "@/lib/LocaleProvider";

function App() {
  return (
    <LocaleProvider>
      <ChatPanel />
    </LocaleProvider>
  );
}

export default App;
