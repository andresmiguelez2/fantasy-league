import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import {
  fetchMyProfiles,
  updatePlayerProfile,
  updateAllPlayerPictures,
  getDefaultAvatarUrl,
  PlayerProfile,
} from "@/lib/api";
import { Pencil, Check, X, Images } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const AVATAR_SEEDS = [
  "Felix", "Aneka", "Jamari", "Kira", "Nora", "Leo", "Mia", "Oscar",
  "Luna", "Kai", "Zara", "Axel", "Ivy", "Rex", "Sage",
];

function getInitials(name?: string | null) {
  const safe = name?.trim();
  if (!safe) return "?";
  return safe
    .split(/\s+/)
    .map((part) => part[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

interface EditState {
  name: string;
  pictureUrl: string;
  customUrl: string;
  useCustomUrl: boolean;
}

interface ProfileCardProps {
  profile: PlayerProfile;
  onSaved: (updatedProfile: PlayerProfile) => void;
}

const ProfileCard = ({ profile, onSaved }: ProfileCardProps) => {
  const { toast } = useToast();
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editState, setEditState] = useState<EditState>({
    name: profile.player_name,
    pictureUrl: profile.picture_url || getDefaultAvatarUrl(profile.player_name),
    customUrl: "",
    useCustomUrl: false,
  });

  const currentAvatarUrl =
    profile.picture_url || getDefaultAvatarUrl(profile.player_name);

  const handleEdit = () => {
    setEditState({
      name: profile.player_name,
      pictureUrl: profile.picture_url || getDefaultAvatarUrl(profile.player_name),
      customUrl: "",
      useCustomUrl: false,
    });
    setEditing(true);
  };

  const handleCancel = () => {
    setEditing(false);
  };

  const handleSave = async () => {
    if (editState.useCustomUrl && !editState.customUrl.trim()) return;

    const finalPictureUrl = editState.useCustomUrl
      ? editState.customUrl.trim()
      : editState.pictureUrl;

    setSaving(true);
    try {
      const updates: { name?: string; picture_url?: string } = {};
      if (editState.name.trim() !== profile.player_name) {
        updates.name = editState.name.trim();
      }
      if (finalPictureUrl !== (profile.picture_url || "")) {
        updates.picture_url = finalPictureUrl;
      }

      if (Object.keys(updates).length === 0) {
        setEditing(false);
        return;
      }

      const result = await updatePlayerProfile(profile.player_id, updates);
      if (result.status === "success") {
        onSaved({
          ...profile,
          player_name: updates.name ?? profile.player_name,
          picture_url: updates.picture_url ?? profile.picture_url,
        });
        setEditing(false);
        toast({ title: "Profile updated" });
      } else {
        toast({
          title: "Failed to update profile",
          description: result.detail,
          variant: "destructive",
        });
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="rounded-lg border border-border p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-muted-foreground">
          {profile.league_name}
        </span>
        {!editing && (
          <Button variant="ghost" size="sm" onClick={handleEdit}>
            <Pencil className="h-3.5 w-3.5 mr-1" />
            Edit
          </Button>
        )}
      </div>

      {!editing ? (
        <div className="flex items-center gap-3">
          <Avatar className="h-12 w-12 border-2 border-secondary/30">
            <AvatarImage src={currentAvatarUrl} />
            <AvatarFallback className="bg-gradient-primary text-white font-semibold text-sm">
              {getInitials(profile.player_name)}
            </AvatarFallback>
          </Avatar>
          <span className="font-semibold">{profile.player_name}</span>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor={`name-${profile.player_id}`}>Player name</Label>
            <Input
              id={`name-${profile.player_id}`}
              value={editState.name}
              onChange={(e) =>
                setEditState((s) => ({ ...s, name: e.target.value }))
              }
              placeholder="Your player name"
            />
          </div>

          <div className="space-y-1.5">
            <Label>Avatar</Label>
            <div className="flex flex-wrap gap-2">
              {AVATAR_SEEDS.map((seed) => {
                const url = getDefaultAvatarUrl(seed);
                const selected =
                  !editState.useCustomUrl && editState.pictureUrl === url;
                return (
                  <button
                    key={seed}
                    type="button"
                    onClick={() =>
                      setEditState((s) => ({
                        ...s,
                        pictureUrl: url,
                        useCustomUrl: false,
                      }))
                    }
                    className={`rounded-full border-2 transition-colors ${
                      selected
                        ? "border-primary"
                        : "border-transparent hover:border-secondary"
                    }`}
                  >
                    <Avatar className="h-9 w-9">
                      <AvatarImage src={url} />
                      <AvatarFallback>{seed[0]}</AvatarFallback>
                    </Avatar>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor={`custom-url-${profile.player_id}`}>
              Or enter a custom image URL
            </Label>
            <Input
              id={`custom-url-${profile.player_id}`}
              value={editState.customUrl}
              onChange={(e) =>
                setEditState((s) => ({
                  ...s,
                  customUrl: e.target.value,
                  useCustomUrl: e.target.value.trim().length > 0,
                }))
              }
              placeholder="https://example.com/my-avatar.png"
            />
            {editState.useCustomUrl && editState.customUrl.trim() && (
              <div className="flex items-center gap-2 mt-1">
                <Avatar className="h-9 w-9 border border-border">
                  <AvatarImage src={editState.customUrl.trim()} />
                  <AvatarFallback>?</AvatarFallback>
                </Avatar>
                <span className="text-xs text-muted-foreground">Preview</span>
              </div>
            )}
          </div>

          <div className="flex gap-2 justify-end">
            <Button
              variant="outline"
              size="sm"
              onClick={handleCancel}
              disabled={saving}
            >
              <X className="h-3.5 w-3.5 mr-1" />
              Cancel
            </Button>
            <Button size="sm" onClick={handleSave} disabled={saving}>
              <Check className="h-3.5 w-3.5 mr-1" />
              {saving ? "Saving…" : "Save"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

interface ProfileDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const ProfileDialog = ({ open, onOpenChange }: ProfileDialogProps) => {
  const { toast } = useToast();
  const [profiles, setProfiles] = useState<PlayerProfile[]>([]);
  const [loading, setLoading] = useState(false);
  const [allPictureOpen, setAllPictureOpen] = useState(false);
  const [allPictureSeed, setAllPictureSeed] = useState<string>(AVATAR_SEEDS[0]);
  const [allPictureCustomUrl, setAllPictureCustomUrl] = useState("");
  const [allPictureUseCustom, setAllPictureUseCustom] = useState(false);
  const [savingAll, setSavingAll] = useState(false);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    fetchMyProfiles()
      .then(setProfiles)
      .catch(() => setProfiles([]))
      .finally(() => setLoading(false));
  }, [open]);

  const handleProfileSaved = (updated: PlayerProfile) => {
    setProfiles((prev) =>
      prev.map((p) => (p.player_id === updated.player_id ? updated : p))
    );
  };

  const handleApplyToAll = async () => {
    const finalUrl = allPictureUseCustom
      ? allPictureCustomUrl.trim()
      : getDefaultAvatarUrl(allPictureSeed);

    if (!finalUrl) return;

    setSavingAll(true);
    try {
      const result = await updateAllPlayerPictures(finalUrl);
      if (result.status === "success") {
        setProfiles((prev) =>
          prev.map((p) => ({ ...p, picture_url: finalUrl }))
        );
        setAllPictureOpen(false);
        toast({ title: "Picture updated for all leagues" });
      } else {
        toast({
          title: "Failed to update pictures",
          description: result.detail,
          variant: "destructive",
        });
      }
    } finally {
      setSavingAll(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>My Profiles</DialogTitle>
          <DialogDescription>
            Manage your player name and picture in each league.
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="py-8 text-center text-muted-foreground text-sm">
            Loading…
          </div>
        ) : profiles.length === 0 ? (
          <div className="py-8 text-center text-muted-foreground text-sm">
            You have not joined any leagues yet.
          </div>
        ) : (
          <div className="space-y-3 py-2">
            {profiles.map((profile) => (
              <ProfileCard
                key={profile.player_id}
                profile={profile}
                onSaved={handleProfileSaved}
              />
            ))}

            <Separator />

            {!allPictureOpen ? (
              <Button
                variant="outline"
                className="w-full"
                onClick={() => setAllPictureOpen(true)}
              >
                <Images className="h-4 w-4 mr-2" />
                Change picture for all leagues
              </Button>
            ) : (
              <div className="rounded-lg border border-border p-4 space-y-3">
                <p className="text-sm font-medium">
                  Change picture for all leagues
                </p>

                <div className="space-y-1.5">
                  <Label>Choose an avatar</Label>
                  <div className="flex flex-wrap gap-2">
                    {AVATAR_SEEDS.map((seed) => {
                      const url = getDefaultAvatarUrl(seed);
                      const selected =
                        !allPictureUseCustom && allPictureSeed === seed;
                      return (
                        <button
                          key={seed}
                          type="button"
                          onClick={() => {
                            setAllPictureSeed(seed);
                            setAllPictureUseCustom(false);
                          }}
                          className={`rounded-full border-2 transition-colors ${
                            selected
                              ? "border-primary"
                              : "border-transparent hover:border-secondary"
                          }`}
                        >
                          <Avatar className="h-9 w-9">
                            <AvatarImage src={url} />
                            <AvatarFallback>{seed[0]}</AvatarFallback>
                          </Avatar>
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="all-custom-url">
                    Or enter a custom image URL
                  </Label>
                  <Input
                    id="all-custom-url"
                    value={allPictureCustomUrl}
                    onChange={(e) => {
                      setAllPictureCustomUrl(e.target.value);
                      setAllPictureUseCustom(e.target.value.trim().length > 0);
                    }}
                    placeholder="https://example.com/my-avatar.png"
                  />
                  {allPictureUseCustom && allPictureCustomUrl.trim() && (
                    <div className="flex items-center gap-2 mt-1">
                      <Avatar className="h-9 w-9 border border-border">
                        <AvatarImage src={allPictureCustomUrl.trim()} />
                        <AvatarFallback>?</AvatarFallback>
                      </Avatar>
                      <span className="text-xs text-muted-foreground">
                        Preview
                      </span>
                    </div>
                  )}
                </div>

                <div className="flex gap-2 justify-end">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setAllPictureOpen(false)}
                    disabled={savingAll}
                  >
                    <X className="h-3.5 w-3.5 mr-1" />
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleApplyToAll}
                    disabled={savingAll}
                  >
                    <Check className="h-3.5 w-3.5 mr-1" />
                    {savingAll ? "Saving…" : "Apply to all leagues"}
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};
