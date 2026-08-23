import { useState, useEffect, useRef } from "react";
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
  uploadPlayerPicture,
  uploadLeaguePlayerPicture,
  getDefaultAvatarUrl,
  resolvePictureUrl,
  PlayerProfile,
} from "@/lib/api";
import { Pencil, Check, X, Images, Upload } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const AVATAR_SEEDS = [
  "Felix",
  "Aneka",
  "Jamari",
  "Kira",
  "Nora",
  "Leo",
  "Mia",
  "Oscar",
  "Luna",
  "Kai",
  "Zara",
  "Axel",
  "Ivy",
  "Rex",
  "Sage",
];

// Must match MAX_PICTURE_BYTES in the backend picture upload endpoints
const MAX_PICTURE_MB = 5;

const isPictureTooLarge = (file: File) => file.size > MAX_PICTURE_MB * 1024 * 1024;

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
  pendingFile: File | null;
  pendingSeed: string | null;
  previewUrl: string | null;
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
    pendingFile: null,
    pendingSeed: null,
    previewUrl: null,
  });
  const fileInputRef = useRef<HTMLInputElement>(null);

  const currentAvatarUrl =
    resolvePictureUrl(profile.picture_url) || getDefaultAvatarUrl(profile.player_name);

  // Seed matching the card's current picture, so the picker can highlight it
  const currentSeed =
    AVATAR_SEEDS.find((seed) => getDefaultAvatarUrl(seed) === profile.picture_url) ?? null;

  const handleEdit = () => {
    setEditState({ name: profile.player_name, pendingFile: null, pendingSeed: null, previewUrl: null });
    setEditing(true);
  };

  const handleCancel = () => {
    if (editState.previewUrl) URL.revokeObjectURL(editState.previewUrl);
    setEditing(false);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null;
    // Reset the input so re-selecting the same file fires onChange again
    e.target.value = "";
    if (!file) return;
    if (isPictureTooLarge(file)) {
      toast({
        title: "Image too large",
        description: `Please choose an image of ${MAX_PICTURE_MB} MB or smaller.`,
        variant: "destructive",
      });
      return;
    }
    const url = URL.createObjectURL(file);
    setEditState((s) => {
      if (s.previewUrl) URL.revokeObjectURL(s.previewUrl);
      return { ...s, pendingFile: file, pendingSeed: null, previewUrl: url };
    });
  };

  const handleSeedSelect = (seed: string) => {
    setEditState((s) => {
      if (s.previewUrl) URL.revokeObjectURL(s.previewUrl);
      return { ...s, pendingFile: null, pendingSeed: seed, previewUrl: null };
    });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      let newPictureUrl: string | undefined;

      if (editState.pendingFile) {
        const result = await uploadLeaguePlayerPicture(profile.player_id, editState.pendingFile);
        if (result.status !== "success") {
          toast({
            title: "Failed to upload picture",
            description: result.detail,
            variant: "destructive",
          });
          return;
        }
        newPictureUrl = result.picture_url;
      }

      // Name and preset changes are combined into a single PATCH call
      const updates: { name?: string; picture_url?: string } = {};
      const newName = editState.name.trim();
      if (newName !== profile.player_name) {
        updates.name = newName;
      }
      const presetUrl = editState.pendingSeed ? getDefaultAvatarUrl(editState.pendingSeed) : null;
      if (!editState.pendingFile && presetUrl && presetUrl !== profile.picture_url) {
        updates.picture_url = presetUrl;
      }

      if (Object.keys(updates).length > 0) {
        const result = await updatePlayerProfile(profile.player_id, updates);
        if (result.status !== "success") {
          toast({ title: "Failed to update profile", description: result.detail, variant: "destructive" });
          // The uploaded picture may already have been saved — keep the card in sync with it
          if (newPictureUrl) {
            onSaved({ ...profile, picture_url: newPictureUrl });
            if (editState.previewUrl) URL.revokeObjectURL(editState.previewUrl);
          }
          return;
        }
      }

      if (!editState.pendingFile && Object.keys(updates).length === 0) {
        setEditing(false);
        return;
      }

      onSaved({
        ...profile,
        player_name: updates.name ?? profile.player_name,
        picture_url: newPictureUrl ?? updates.picture_url ?? profile.picture_url,
      });
      if (editState.previewUrl) URL.revokeObjectURL(editState.previewUrl);
      setEditing(false);
      toast({ title: "Profile updated" });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="rounded-lg border border-border p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-muted-foreground">{profile.league_name}</span>
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
              onChange={(e) => setEditState((s) => ({ ...s, name: e.target.value }))}
              placeholder="Your player name"
            />
          </div>

          <div className="space-y-1.5">
            <Label>Profile picture</Label>
            <div className="flex items-center gap-3">
              <Avatar className="h-12 w-12 border border-border">
                <AvatarImage
                  src={
                    editState.previewUrl ??
                    (editState.pendingSeed
                      ? getDefaultAvatarUrl(editState.pendingSeed)
                      : currentAvatarUrl)
                  }
                />
                <AvatarFallback>{getInitials(profile.player_name)}</AvatarFallback>
              </Avatar>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="h-3.5 w-3.5 mr-1" />
                Upload from device
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleFileChange}
              />
            </div>

            <div className="space-y-1.5 pt-1">
              <Label>Or choose an avatar</Label>
              <div className="flex flex-wrap gap-2">
                {AVATAR_SEEDS.map((seed) => {
                  const url = getDefaultAvatarUrl(seed);
                  const selected =
                    !editState.pendingFile &&
                    (editState.pendingSeed ?? currentSeed) === seed;
                  return (
                    <button
                      key={seed}
                      type="button"
                      aria-label={`Use the ${seed} avatar`}
                      onClick={() => handleSeedSelect(seed)}
                      className={`rounded-full border-2 p-0.5 transition-colors ${
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

            <p className="text-xs text-muted-foreground">
              This picture applies only to this league. Use &quot;Change picture for all
              leagues&quot; below to update every league at once.
            </p>
          </div>

          <div className="flex gap-2 justify-end">
            <Button variant="outline" size="sm" onClick={handleCancel} disabled={saving}>
              <X className="h-3.5 w-3.5 mr-1" />
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={handleSave}
              disabled={saving || !editState.name.trim()}
            >
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
  const [allPictureFile, setAllPictureFile] = useState<File | null>(null);
  const [allPicturePreviewUrl, setAllPicturePreviewUrl] = useState<string | null>(null);
  const [savingAll, setSavingAll] = useState(false);
  const allFileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    fetchMyProfiles()
      .then(setProfiles)
      .catch(() => setProfiles([]))
      .finally(() => setLoading(false));
  }, [open]);

  const handleProfileSaved = (updated: PlayerProfile) => {
    setProfiles((prev) => prev.map((p) => (p.player_id === updated.player_id ? updated : p)));
  };

  const handleAllFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null;
    // Reset the input so re-selecting the same file fires onChange again
    e.target.value = "";
    if (!file) return;
    if (isPictureTooLarge(file)) {
      toast({
        title: "Image too large",
        description: `Please choose an image of ${MAX_PICTURE_MB} MB or smaller.`,
        variant: "destructive",
      });
      return;
    }
    const url = URL.createObjectURL(file);
    setAllPictureFile(file);
    if (allPicturePreviewUrl) URL.revokeObjectURL(allPicturePreviewUrl);
    setAllPicturePreviewUrl(url);
  };

  const handleApplyToAll = async () => {
    setSavingAll(true);
    try {
      let newPictureUrl: string;

      if (allPictureFile) {
        const result = await uploadPlayerPicture(allPictureFile);
        if (result.status !== "success" || !result.picture_url) {
          toast({
            title: "Failed to upload picture",
            description: result.detail,
            variant: "destructive",
          });
          return;
        }
        newPictureUrl = result.picture_url;
      } else {
        const finalUrl = getDefaultAvatarUrl(allPictureSeed);
        const result = await updateAllPlayerPictures(finalUrl);
        if (result.status !== "success") {
          toast({
            title: "Failed to update pictures",
            description: result.detail,
            variant: "destructive",
          });
          return;
        }
        newPictureUrl = finalUrl;
      }

      setProfiles((prev) => prev.map((p) => ({ ...p, picture_url: newPictureUrl })));
      if (allPicturePreviewUrl) URL.revokeObjectURL(allPicturePreviewUrl);
      setAllPictureFile(null);
      setAllPicturePreviewUrl(null);
      setAllPictureOpen(false);
      toast({ title: "Picture updated for all leagues" });
    } finally {
      setSavingAll(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>My Profiles</DialogTitle>
          <DialogDescription>Manage your player name and picture in each league.</DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="py-8 text-center text-muted-foreground text-sm">Loading…</div>
        ) : profiles.length === 0 ? (
          <div className="py-8 text-center text-muted-foreground text-sm">
            You have not joined any leagues yet.
          </div>
        ) : (
          <div className="space-y-3 py-2">
            {profiles.map((profile) => (
              <ProfileCard key={profile.player_id} profile={profile} onSaved={handleProfileSaved} />
            ))}

            <Separator />

            {!allPictureOpen ? (
              <Button variant="outline" className="w-full" onClick={() => setAllPictureOpen(true)}>
                <Images className="h-4 w-4 mr-2" />
                Change picture for all leagues
              </Button>
            ) : (
              <div className="rounded-lg border border-border p-4 space-y-3">
                <p className="text-sm font-medium">Change picture for all leagues</p>

                <div className="space-y-1.5">
                  <Label>Choose an avatar</Label>
                  <div className="flex flex-wrap gap-2">
                    {AVATAR_SEEDS.map((seed) => {
                      const url = getDefaultAvatarUrl(seed);
                      const selected = !allPictureFile && allPictureSeed === seed;
                      return (
                        <button
                          key={seed}
                          type="button"
                          aria-label={`Use the ${seed} avatar`}
                          onClick={() => {
                            setAllPictureSeed(seed);
                            setAllPictureFile(null);
                            if (allPicturePreviewUrl) URL.revokeObjectURL(allPicturePreviewUrl);
                            setAllPicturePreviewUrl(null);
                          }}
                          className={`rounded-full border-2 p-0.5 transition-colors ${
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
                  <Label>Or upload from device</Label>
                  <div className="flex items-center gap-3">
                    {allPicturePreviewUrl && (
                      <Avatar className="h-9 w-9 border border-border">
                        <AvatarImage src={allPicturePreviewUrl} />
                        <AvatarFallback>?</AvatarFallback>
                      </Avatar>
                    )}
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="max-w-full min-w-0"
                      onClick={() => allFileInputRef.current?.click()}
                    >
                      <Upload className="h-3.5 w-3.5 mr-1" />
                      {allPictureFile ? (
                        <span className="truncate min-w-0">{allPictureFile.name}</span>
                      ) : (
                        "Choose file"
                      )}
                    </Button>
                    <input
                      ref={allFileInputRef}
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={handleAllFileChange}
                    />
                  </div>
                </div>

                <div className="flex gap-2 justify-end">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      if (allPicturePreviewUrl) URL.revokeObjectURL(allPicturePreviewUrl);
                      setAllPictureFile(null);
                      setAllPicturePreviewUrl(null);
                      setAllPictureOpen(false);
                    }}
                    disabled={savingAll}
                  >
                    <X className="h-3.5 w-3.5 mr-1" />
                    Cancel
                  </Button>
                  <Button size="sm" onClick={handleApplyToAll} disabled={savingAll}>
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
