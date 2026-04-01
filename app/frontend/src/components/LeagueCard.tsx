import { useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Trophy } from "lucide-react";
import { setActiveLeagueContext } from "@/lib/api";

interface LeagueCardProps {
  id: string;
  name: string;
}

const gradients = [
  "bg-gradient-to-br from-purple-600 to-blue-500",
  "bg-gradient-to-br from-pink-600 to-purple-500",
  "bg-gradient-to-br from-cyan-600 to-blue-500"
];

export const LeagueCard = ({ id, name }: LeagueCardProps) => {
  const navigate = useNavigate();
  const gradientIndex = parseInt(id) % gradients.length;

  const handleClick = async () => {
    try {
      await setActiveLeagueContext(id);
    } catch (error) {
      console.error("Failed to set active league context:", error);
    }
    navigate(`/league/${id}`);
  };
  
  return (
    <Card
      onClick={handleClick}
      className={`p-8 cursor-pointer hover-lift fade-in border-0 ${gradients[gradientIndex]} relative overflow-hidden group`}
    >
      <div className="absolute inset-0 bg-black/20 group-hover:bg-black/10 transition-colors" />
      <div className="relative flex items-center gap-4">
        <div className="p-3 bg-white/20 rounded-full backdrop-blur-sm">
          <Trophy className="w-8 h-8 text-white" />
        </div>
        <h3 className="text-2xl font-bold text-white">{name}</h3>
      </div>
    </Card>
  );
};
