import { useEffect, useState, useCallback } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useNavigate, useLocation, Link, useParams } from "react-router-dom";
import axios from "axios";
import { Toaster, toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Calendar } from "@/components/ui/calendar";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Slider } from "@/components/ui/slider";
import { Mountain, Calendar as CalendarIcon, Clock, Users, Euro, MapPin, User, LogOut, ChevronRight, Snowflake, Star, Check, X, Award, Filter, Repeat, TrendingUp } from "lucide-react";
import { format, addWeeks } from "date-fns";
import { fr } from "date-fns/locale";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const AUTH_URL = "https://auth.emergentagent.com";

// Auth Context
const useAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/auth/me`, { withCredentials: true });
      setUser(response.data);
    } catch (e) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = async () => {
    try {
      await axios.post(`${API}/auth/logout`, {}, { withCredentials: true });
      setUser(null);
      toast.success("Déconnecté");
    } catch (e) {
      console.error(e);
    }
  };

  return { user, setUser, loading, checkAuth, logout };
};

// Stations Hook
const useStations = () => {
  const [stations, setStations] = useState([]);

  useEffect(() => {
    const fetchStations = async () => {
      try {
        const response = await axios.get(`${API}/stations`);
        setStations(response.data);
      } catch (e) {
        console.error(e);
      }
    };
    fetchStations();
  }, []);

  return stations;
};

// Header Component
const Header = ({ user, logout }) => {
  const navigate = useNavigate();
  const redirectUrl = encodeURIComponent(`${window.location.origin}/auth-callback`);
  const loginUrl = `${AUTH_URL}/?redirect=${redirectUrl}`;

  return (
    <header className="header" data-testid="header">
      <div className="header-container">
        <Link to="/" className="logo" data-testid="logo">
          <Mountain className="logo-icon" />
          <span>SkiMonitor</span>
        </Link>
        
        <nav className="nav-links">
          <Link to="/instructors" data-testid="nav-instructors">Moniteurs</Link>
          <Link to="/lessons" data-testid="nav-lessons">Cours</Link>
        </nav>

        <div className="header-actions">
          {user ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="user-menu" data-testid="user-menu">
                  <Avatar className="user-avatar">
                    <AvatarImage src={user.picture} alt={user.name} />
                    <AvatarFallback>{user.name?.charAt(0)}</AvatarFallback>
                  </Avatar>
                  <span className="user-name">{user.name}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => navigate("/dashboard")} data-testid="menu-dashboard">
                  <User className="menu-icon" /> Mon espace
                </DropdownMenuItem>
                {user.role === "instructor" && (
                  <DropdownMenuItem onClick={() => navigate("/instructor-dashboard")} data-testid="menu-instructor">
                    <Award className="menu-icon" /> Espace moniteur
                  </DropdownMenuItem>
                )}
                {user.role === "admin" && (
                  <DropdownMenuItem onClick={() => navigate("/admin")} data-testid="menu-admin">
                    <Star className="menu-icon" /> Administration
                  </DropdownMenuItem>
                )}
                <DropdownMenuItem onClick={logout} data-testid="menu-logout">
                  <LogOut className="menu-icon" /> Déconnexion
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Button onClick={() => window.location.href = loginUrl} className="login-btn" data-testid="login-btn">
              Connexion
            </Button>
          )}
        </div>
      </div>
    </header>
  );
};

// Landing Page
const Landing = ({ user }) => {
  const navigate = useNavigate();
  const redirectUrl = encodeURIComponent(`${window.location.origin}/auth-callback`);
  const loginUrl = `${AUTH_URL}/?redirect=${redirectUrl}`;

  return (
    <div className="landing" data-testid="landing-page">
      <section className="hero">
        <div className="hero-content">
          <div className="hero-badge">
            <Snowflake size={14} />
            <span>Plateforme de réservation</span>
          </div>
          <h1>Réservez votre cours de ski en quelques clics</h1>
          <p>Trouvez le moniteur idéal et réservez vos cours de ski ou snowboard directement en ligne</p>
          <div className="hero-actions">
            <Button onClick={() => navigate("/instructors")} size="lg" className="primary-btn" data-testid="cta-instructors">
              Voir les moniteurs <ChevronRight size={18} />
            </Button>
            {!user && (
              <Button onClick={() => window.location.href = loginUrl} variant="outline" size="lg" className="secondary-btn" data-testid="cta-register">
                Devenir moniteur
              </Button>
            )}
          </div>
        </div>
        <div className="hero-visual">
          <div className="hero-card">
            <Mountain size={80} />
          </div>
        </div>
      </section>

      <section className="features">
        <h2>Pourquoi SkiMonitor ?</h2>
        <div className="features-grid">
          <Card className="feature-card">
            <CardHeader>
              <div className="feature-icon"><CalendarIcon size={24} /></div>
              <CardTitle>Réservation simple</CardTitle>
            </CardHeader>
            <CardContent>
              <p>Réservez en quelques clics, choisissez votre créneau et payez en ligne de manière sécurisée</p>
            </CardContent>
          </Card>
          <Card className="feature-card">
            <CardHeader>
              <div className="feature-icon"><Users size={24} /></div>
              <CardTitle>Moniteurs certifiés</CardTitle>
            </CardHeader>
            <CardContent>
              <p>Tous nos moniteurs sont validés et certifiés pour garantir des cours de qualité</p>
            </CardContent>
          </Card>
          <Card className="feature-card">
            <CardHeader>
              <div className="feature-icon"><Award size={24} /></div>
              <CardTitle>Cours variés</CardTitle>
            </CardHeader>
            <CardContent>
              <p>Cours particuliers ou collectifs, ski ou snowboard, débutants ou experts</p>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
};

// Auth Callback
const AuthCallback = ({ setUser, checkAuth }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [processing, setProcessing] = useState(true);

  useEffect(() => {
    const processAuth = async () => {
      const hash = window.location.hash;
      const sessionIdMatch = hash.match(/session_id=([^&]+)/);
      
      if (sessionIdMatch) {
        const sessionId = sessionIdMatch[1];
        try {
          const response = await axios.post(`${API}/auth/session`, { session_id: sessionId }, { withCredentials: true });
          setUser(response.data);
          toast.success(`Bienvenue ${response.data.name} !`);
          window.history.replaceState(null, "", window.location.pathname);
          navigate("/dashboard");
        } catch (e) {
          console.error(e);
          toast.error("Erreur d'authentification");
          navigate("/");
        }
      } else {
        await checkAuth();
        navigate("/dashboard");
      }
      setProcessing(false);
    };

    processAuth();
  }, [location, navigate, setUser, checkAuth]);

  if (processing) {
    return (
      <div className="loading-page" data-testid="auth-loading">
        <div className="loading-spinner"></div>
        <p>Connexion en cours...</p>
      </div>
    );
  }

  return null;
};

// Instructors List with Filters
const InstructorsList = () => {
  const [instructors, setInstructors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    station_id: "all",
    specialty: "all",
    level: "all",
    maxPrice: 200
  });
  const stations = useStations();

  const specialties = ["Ski alpin", "Snowboard", "Freestyle", "Ski de fond", "Hors-piste"];
  const levels = ["Débutant", "Intermédiaire", "Avancé", "Expert"];

  useEffect(() => {
    const fetchInstructors = async () => {
      try {
        const params = {};
        if (filters.station_id && filters.station_id !== "all") params.station_id = filters.station_id;
        if (filters.specialty && filters.specialty !== "all") params.specialty = filters.specialty;
        if (filters.level && filters.level !== "all") params.level = filters.level;
        if (filters.maxPrice < 200) params.max_price = filters.maxPrice;
        
        const response = await axios.get(`${API}/instructors`, { params });
        setInstructors(response.data);
      } catch (e) {
        toast.error("Erreur de chargement");
      } finally {
        setLoading(false);
      }
    };
    fetchInstructors();
  }, [filters]);

  const clearFilters = () => {
    setFilters({ station_id: "all", specialty: "all", level: "all", maxPrice: 200 });
  };

  if (loading) return <div className="loading-page"><div className="loading-spinner"></div></div>;

  return (
    <div className="page-container" data-testid="instructors-page">
      <div className="page-header">
        <div>
          <h1>Nos moniteurs</h1>
          <p>Découvrez nos moniteurs certifiés et trouvez celui qui correspond à vos besoins</p>
        </div>
        <Button variant="outline" onClick={() => setShowFilters(!showFilters)} className="filter-toggle" data-testid="toggle-filters">
          <Filter size={18} /> Filtres
        </Button>
      </div>

      {showFilters && (
        <Card className="filters-card" data-testid="filters-panel">
          <CardContent>
            <div className="filters-grid">
              <div className="filter-group">
                <Label>Station</Label>
                <Select value={filters.station_id} onValueChange={(v) => setFilters({ ...filters, station_id: v })}>
                  <SelectTrigger data-testid="filter-station">
                    <SelectValue placeholder="Toutes les stations" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Toutes les stations</SelectItem>
                    {stations.map((s) => (
                      <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="filter-group">
                <Label>Spécialité</Label>
                <Select value={filters.specialty} onValueChange={(v) => setFilters({ ...filters, specialty: v })}>
                  <SelectTrigger data-testid="filter-specialty">
                    <SelectValue placeholder="Toutes" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Toutes</SelectItem>
                    {specialties.map((s) => (
                      <SelectItem key={s} value={s}>{s}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="filter-group">
                <Label>Niveau</Label>
                <Select value={filters.level} onValueChange={(v) => setFilters({ ...filters, level: v })}>
                  <SelectTrigger data-testid="filter-level">
                    <SelectValue placeholder="Tous niveaux" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Tous niveaux</SelectItem>
                    {levels.map((l) => (
                      <SelectItem key={l} value={l}>{l}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="filter-group">
                <Label>Prix max: {filters.maxPrice}€/h</Label>
                <Slider
                  value={[filters.maxPrice]}
                  onValueChange={([v]) => setFilters({ ...filters, maxPrice: v })}
                  min={20}
                  max={200}
                  step={10}
                  data-testid="filter-price"
                />
              </div>
            </div>
            <Button variant="ghost" onClick={clearFilters} className="clear-filters">Effacer les filtres</Button>
          </CardContent>
        </Card>
      )}

      {instructors.length === 0 ? (
        <Card className="empty-state">
          <CardContent>
            <Users size={48} />
            <p>Aucun moniteur disponible avec ces critères</p>
            <Button variant="outline" onClick={clearFilters}>Effacer les filtres</Button>
          </CardContent>
        </Card>
      ) : (
        <div className="instructors-grid">
          {instructors.map((instructor) => (
            <Card key={instructor.id} className="instructor-card" data-testid={`instructor-${instructor.id}`}>
              <CardHeader>
                <div className="instructor-header">
                  <Avatar className="instructor-avatar">
                    <AvatarImage src={instructor.user?.picture} />
                    <AvatarFallback>{instructor.user?.name?.charAt(0)}</AvatarFallback>
                  </Avatar>
                  <div>
                    <CardTitle>{instructor.user?.name}</CardTitle>
                    <CardDescription>{instructor.hourly_rate}€/h</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {instructor.station && (
                  <div className="instructor-station">
                    <MapPin size={14} />
                    <span>{instructor.station.name}</span>
                  </div>
                )}
                <p className="instructor-bio">{instructor.bio || "Moniteur de ski expérimenté"}</p>
                <div className="instructor-tags">
                  {instructor.specialties?.map((s) => (
                    <Badge key={s} variant="secondary">{s}</Badge>
                  ))}
                  {instructor.ski_levels?.map((l) => (
                    <Badge key={l} variant="outline">{l}</Badge>
                  ))}
                </div>
              </CardContent>
              <CardFooter>
                <Link to={`/instructor/${instructor.id}`}>
                  <Button className="view-btn" data-testid={`view-instructor-${instructor.id}`}>Voir les cours</Button>
                </Link>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

// Instructor Detail
const InstructorDetail = ({ user }) => {
  const { id } = useParams();
  const [instructor, setInstructor] = useState(null);
  const [lessons, setLessons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [instRes, lessonsRes] = await Promise.all([
          axios.get(`${API}/instructors/${id}`),
          axios.get(`${API}/lessons`, { params: { instructor_id: id } })
        ]);
        setInstructor(instRes.data);
        setLessons(lessonsRes.data);
      } catch (e) {
        toast.error("Erreur de chargement");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id]);

  const handleBook = async (lesson) => {
    if (!user) {
      const redirectUrl = encodeURIComponent(`${window.location.origin}/auth-callback`);
      window.location.href = `${AUTH_URL}/?redirect=${redirectUrl}`;
      return;
    }

    try {
      await axios.post(`${API}/bookings`, { lesson_id: lesson.id, participants: 1 }, { withCredentials: true });
      toast.success("Réservation effectuée !");
      navigate("/dashboard");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Erreur de réservation");
    }
  };

  if (loading) return <div className="loading-page"><div className="loading-spinner"></div></div>;
  if (!instructor) return <div className="page-container"><p>Moniteur non trouvé</p></div>;

  const filteredLessons = lessons.filter(l => l.date === format(selectedDate, "yyyy-MM-dd"));

  return (
    <div className="page-container" data-testid="instructor-detail-page">
      <Card className="instructor-profile">
        <CardHeader>
          <div className="instructor-header large">
            <Avatar className="instructor-avatar large">
              <AvatarImage src={instructor.user?.picture} />
              <AvatarFallback>{instructor.user?.name?.charAt(0)}</AvatarFallback>
            </Avatar>
            <div>
              <CardTitle className="large">{instructor.user?.name}</CardTitle>
              <CardDescription className="large">{instructor.hourly_rate}€/h</CardDescription>
              {instructor.station && (
                <div className="instructor-station">
                  <MapPin size={14} />
                  <span>{instructor.station.name}</span>
                </div>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p>{instructor.bio}</p>
          <div className="instructor-tags">
            {instructor.specialties?.map((s) => <Badge key={s} variant="secondary">{s}</Badge>)}
            {instructor.ski_levels?.map((l) => <Badge key={l} variant="outline">{l}</Badge>)}
          </div>
        </CardContent>
      </Card>

      <div className="lessons-section">
        <h2>Cours disponibles</h2>
        <div className="lessons-layout">
          <div className="calendar-wrapper">
            <Calendar
              mode="single"
              selected={selectedDate}
              onSelect={(date) => date && setSelectedDate(date)}
              locale={fr}
              className="calendar"
            />
          </div>
          <div className="lessons-list">
            <h3>{format(selectedDate, "EEEE d MMMM", { locale: fr })}</h3>
            {filteredLessons.length === 0 ? (
              <p className="no-lessons">Aucun cours disponible ce jour</p>
            ) : (
              filteredLessons.map((lesson) => (
                <Card key={lesson.id} className="lesson-card" data-testid={`lesson-${lesson.id}`}>
                  <CardContent>
                    <div className="lesson-info">
                      <h4>
                        {lesson.title}
                        {lesson.is_recurring && <Repeat size={14} className="recurring-icon" />}
                      </h4>
                      <div className="lesson-meta">
                        <span><Clock size={14} /> {lesson.start_time} - {lesson.end_time}</span>
                        <span><Users size={14} /> {lesson.current_participants}/{lesson.max_participants}</span>
                        <span><Euro size={14} /> {lesson.price}€</span>
                      </div>
                      <Badge variant={lesson.lesson_type === "private" ? "default" : "secondary"}>
                        {lesson.lesson_type === "private" ? "Particulier" : "Collectif"}
                      </Badge>
                    </div>
                    <Button onClick={() => handleBook(lesson)} disabled={lesson.status === "full"} data-testid={`book-lesson-${lesson.id}`}>
                      {lesson.status === "full" ? "Complet" : "Réserver"}
                    </Button>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Lessons List with Filters
const LessonsList = ({ user }) => {
  const [lessons, setLessons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    lesson_type: "all",
    station_id: "all",
    level: "all",
    maxPrice: 200
  });
  const stations = useStations();
  const navigate = useNavigate();

  const levels = ["Débutant", "Intermédiaire", "Avancé", "Expert"];

  useEffect(() => {
    const fetchLessons = async () => {
      try {
        const params = {};
        if (filters.lesson_type) params.lesson_type = filters.lesson_type;
        if (filters.station_id) params.station_id = filters.station_id;
        if (filters.level) params.level = filters.level;
        if (filters.maxPrice < 200) params.max_price = filters.maxPrice;
        
        const response = await axios.get(`${API}/lessons`, { params });
        setLessons(response.data);
      } catch (e) {
        toast.error("Erreur de chargement");
      } finally {
        setLoading(false);
      }
    };
    fetchLessons();
  }, [filters]);

  const handleBook = async (lesson) => {
    if (!user) {
      const redirectUrl = encodeURIComponent(`${window.location.origin}/auth-callback`);
      window.location.href = `${AUTH_URL}/?redirect=${redirectUrl}`;
      return;
    }

    try {
      await axios.post(`${API}/bookings`, { lesson_id: lesson.id, participants: 1 }, { withCredentials: true });
      toast.success("Réservation effectuée !");
      navigate("/dashboard");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Erreur de réservation");
    }
  };

  const clearFilters = () => {
    setFilters({ lesson_type: "", station_id: "", level: "", maxPrice: 200 });
  };

  if (loading) return <div className="loading-page"><div className="loading-spinner"></div></div>;

  const filteredLessons = lessons.filter(l => l.date === format(selectedDate, "yyyy-MM-dd"));

  return (
    <div className="page-container" data-testid="lessons-page">
      <div className="page-header">
        <div>
          <h1>Cours disponibles</h1>
          <p>Parcourez tous les cours et réservez celui qui vous convient</p>
        </div>
        <Button variant="outline" onClick={() => setShowFilters(!showFilters)} className="filter-toggle">
          <Filter size={18} /> Filtres
        </Button>
      </div>

      {showFilters && (
        <Card className="filters-card">
          <CardContent>
            <div className="filters-grid">
              <div className="filter-group">
                <Label>Type de cours</Label>
                <Select value={filters.lesson_type} onValueChange={(v) => setFilters({ ...filters, lesson_type: v })}>
                  <SelectTrigger data-testid="filter-lesson-type">
                    <SelectValue placeholder="Tous les cours" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Tous les cours</SelectItem>
                    <SelectItem value="private">Particuliers</SelectItem>
                    <SelectItem value="group">Collectifs</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="filter-group">
                <Label>Station</Label>
                <Select value={filters.station_id} onValueChange={(v) => setFilters({ ...filters, station_id: v })}>
                  <SelectTrigger>
                    <SelectValue placeholder="Toutes les stations" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Toutes les stations</SelectItem>
                    {stations.map((s) => (
                      <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="filter-group">
                <Label>Niveau</Label>
                <Select value={filters.level} onValueChange={(v) => setFilters({ ...filters, level: v })}>
                  <SelectTrigger>
                    <SelectValue placeholder="Tous niveaux" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Tous niveaux</SelectItem>
                    {levels.map((l) => (
                      <SelectItem key={l} value={l}>{l}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="filter-group">
                <Label>Prix max: {filters.maxPrice}€</Label>
                <Slider
                  value={[filters.maxPrice]}
                  onValueChange={([v]) => setFilters({ ...filters, maxPrice: v })}
                  min={20}
                  max={200}
                  step={10}
                />
              </div>
            </div>
            <Button variant="ghost" onClick={clearFilters} className="clear-filters">Effacer les filtres</Button>
          </CardContent>
        </Card>
      )}

      <div className="lessons-layout">
        <div className="calendar-wrapper">
          <Calendar
            mode="single"
            selected={selectedDate}
            onSelect={(date) => date && setSelectedDate(date)}
            locale={fr}
            className="calendar"
          />
        </div>
        <div className="lessons-list">
          <h3>{format(selectedDate, "EEEE d MMMM yyyy", { locale: fr })}</h3>
          {filteredLessons.length === 0 ? (
            <Card className="empty-state">
              <CardContent>
                <CalendarIcon size={48} />
                <p>Aucun cours disponible ce jour</p>
              </CardContent>
            </Card>
          ) : (
            filteredLessons.map((lesson) => (
              <Card key={lesson.id} className="lesson-card with-instructor" data-testid={`lesson-${lesson.id}`}>
                <CardContent>
                  <div className="lesson-instructor">
                    <Avatar>
                      <AvatarImage src={lesson.instructor?.user?.picture} />
                      <AvatarFallback>{lesson.instructor?.user?.name?.charAt(0)}</AvatarFallback>
                    </Avatar>
                    <div>
                      <span>{lesson.instructor?.user?.name}</span>
                      {lesson.instructor?.station && (
                        <span className="instructor-station-small">
                          <MapPin size={12} /> {lesson.instructor.station.name}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="lesson-info">
                    <h4>
                      {lesson.title}
                      {lesson.is_recurring && <Repeat size={14} className="recurring-icon" />}
                    </h4>
                    <div className="lesson-meta">
                      <span><Clock size={14} /> {lesson.start_time} - {lesson.end_time}</span>
                      <span><Users size={14} /> {lesson.current_participants}/{lesson.max_participants}</span>
                      <span><Euro size={14} /> {lesson.price}€</span>
                    </div>
                    <Badge variant={lesson.lesson_type === "private" ? "default" : "secondary"}>
                      {lesson.lesson_type === "private" ? "Particulier" : "Collectif"}
                    </Badge>
                  </div>
                  <Button onClick={() => handleBook(lesson)} disabled={lesson.status === "full"} data-testid={`book-lesson-${lesson.id}`}>
                    {lesson.status === "full" ? "Complet" : "Réserver"}
                  </Button>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

// User Dashboard
const Dashboard = ({ user }) => {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    if (!user) {
      navigate("/");
      return;
    }
    const fetchBookings = async () => {
      try {
        const response = await axios.get(`${API}/bookings`, { withCredentials: true });
        setBookings(response.data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchBookings();
  }, [user, navigate]);

  const handleCancel = async (bookingId) => {
    try {
      await axios.delete(`${API}/bookings/${bookingId}`, { withCredentials: true });
      setBookings(bookings.filter(b => b.id !== bookingId));
      toast.success("Réservation annulée");
    } catch (e) {
      toast.error("Erreur lors de l'annulation");
    }
  };

  const handlePayment = async (booking) => {
    try {
      const response = await axios.post(`${API}/payments/checkout`, {
        booking_id: booking.id,
        origin_url: window.location.origin
      }, { withCredentials: true });
      window.location.href = response.data.url;
    } catch (e) {
      toast.error("Erreur lors du paiement");
    }
  };

  if (loading) return <div className="loading-page"><div className="loading-spinner"></div></div>;

  return (
    <div className="page-container" data-testid="dashboard-page">
      <div className="page-header">
        <h1>Mon espace</h1>
        <p>Gérez vos réservations</p>
      </div>

      {user?.role === "client" && (
        <Card className="become-instructor-card">
          <CardContent>
            <div className="become-instructor-content">
              <div>
                <h3>Vous êtes moniteur ?</h3>
                <p>Inscrivez-vous pour proposer vos cours sur la plateforme</p>
              </div>
              <Button onClick={() => navigate("/become-instructor")} data-testid="become-instructor-btn">
                Devenir moniteur
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <h2>Mes réservations</h2>
      {bookings.length === 0 ? (
        <Card className="empty-state">
          <CardContent>
            <CalendarIcon size={48} />
            <p>Aucune réservation</p>
            <Button onClick={() => navigate("/lessons")}>Voir les cours</Button>
          </CardContent>
        </Card>
      ) : (
        <div className="bookings-list">
          {bookings.map((booking) => (
            <Card key={booking.id} className={`booking-card ${booking.status}`} data-testid={`booking-${booking.id}`}>
              <CardContent>
                <div className="booking-info">
                  <div className="booking-instructor">
                    <Avatar>
                      <AvatarImage src={booking.lesson?.instructor?.user?.picture} />
                      <AvatarFallback>{booking.lesson?.instructor?.user?.name?.charAt(0)}</AvatarFallback>
                    </Avatar>
                    <div>
                      <h4>{booking.lesson?.title}</h4>
                      <span className="instructor-name">{booking.lesson?.instructor?.user?.name}</span>
                      {booking.lesson?.instructor?.station && (
                        <span className="instructor-station-small">
                          <MapPin size={12} /> {booking.lesson.instructor.station.name}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="booking-meta">
                    <span><CalendarIcon size={14} /> {booking.lesson?.date}</span>
                    <span><Clock size={14} /> {booking.lesson?.start_time} - {booking.lesson?.end_time}</span>
                    <span><Euro size={14} /> {booking.lesson?.price}€</span>
                  </div>
                  <div className="booking-status">
                    <Badge variant={booking.status === "confirmed" ? "default" : booking.status === "cancelled" ? "destructive" : "secondary"}>
                      {booking.status === "confirmed" ? "Confirmé" : booking.status === "cancelled" ? "Annulé" : "En attente"}
                    </Badge>
                    <Badge variant={booking.payment_status === "paid" ? "default" : "outline"}>
                      {booking.payment_status === "paid" ? "Payé" : "Non payé"}
                    </Badge>
                  </div>
                </div>
                <div className="booking-actions">
                  {booking.status !== "cancelled" && booking.payment_status !== "paid" && (
                    <Button onClick={() => handlePayment(booking)} data-testid={`pay-booking-${booking.id}`}>
                      Payer
                    </Button>
                  )}
                  {booking.status !== "cancelled" && (
                    <Button variant="outline" onClick={() => handleCancel(booking.id)} data-testid={`cancel-booking-${booking.id}`}>
                      Annuler
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

// Become Instructor Form
const BecomeInstructor = ({ user, setUser }) => {
  const [formData, setFormData] = useState({
    bio: "",
    specialties: [],
    ski_levels: [],
    hourly_rate: 50,
    station_id: ""
  });
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();
  const stations = useStations();

  const specialtiesOptions = ["Ski alpin", "Snowboard", "Freestyle", "Ski de fond", "Hors-piste"];
  const levelsOptions = ["Débutant", "Intermédiaire", "Avancé", "Expert"];

  const handleSpecialtyChange = (specialty, checked) => {
    setFormData(prev => ({
      ...prev,
      specialties: checked
        ? [...prev.specialties, specialty]
        : prev.specialties.filter(s => s !== specialty)
    }));
  };

  const handleLevelChange = (level, checked) => {
    setFormData(prev => ({
      ...prev,
      ski_levels: checked
        ? [...prev.ski_levels, level]
        : prev.ski_levels.filter(l => l !== level)
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      await axios.post(`${API}/instructors`, formData, { withCredentials: true });
      toast.success("Demande envoyée ! En attente de validation.");
      setUser({ ...user, role: "instructor" });
      navigate("/instructor-dashboard");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Erreur lors de l'inscription");
    } finally {
      setSubmitting(false);
    }
  };

  if (!user) {
    navigate("/");
    return null;
  }

  return (
    <div className="page-container" data-testid="become-instructor-page">
      <div className="page-header">
        <h1>Devenir moniteur</h1>
        <p>Remplissez ce formulaire pour proposer vos cours</p>
      </div>

      <Card className="form-card">
        <CardContent>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <Label htmlFor="station">Station de ski</Label>
              <Select value={formData.station_id} onValueChange={(v) => setFormData({ ...formData, station_id: v })}>
                <SelectTrigger data-testid="instructor-station">
                  <SelectValue placeholder="Sélectionnez votre station" />
                </SelectTrigger>
                <SelectContent>
                  {stations.map((s) => (
                    <SelectItem key={s.id} value={s.id}>{s.name} ({s.region})</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="form-group">
              <Label htmlFor="bio">Présentation</Label>
              <Textarea
                id="bio"
                value={formData.bio}
                onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                placeholder="Décrivez votre expérience et votre approche pédagogique..."
                rows={4}
                data-testid="instructor-bio"
              />
            </div>

            <div className="form-group">
              <Label>Spécialités</Label>
              <div className="checkbox-group">
                {specialtiesOptions.map((specialty) => (
                  <div key={specialty} className="checkbox-item">
                    <Checkbox
                      id={specialty}
                      checked={formData.specialties.includes(specialty)}
                      onCheckedChange={(checked) => handleSpecialtyChange(specialty, checked)}
                      data-testid={`specialty-${specialty}`}
                    />
                    <Label htmlFor={specialty}>{specialty}</Label>
                  </div>
                ))}
              </div>
            </div>

            <div className="form-group">
              <Label>Niveaux enseignés</Label>
              <div className="checkbox-group">
                {levelsOptions.map((level) => (
                  <div key={level} className="checkbox-item">
                    <Checkbox
                      id={level}
                      checked={formData.ski_levels.includes(level)}
                      onCheckedChange={(checked) => handleLevelChange(level, checked)}
                      data-testid={`level-${level}`}
                    />
                    <Label htmlFor={level}>{level}</Label>
                  </div>
                ))}
              </div>
            </div>

            <div className="form-group">
              <Label htmlFor="rate">Tarif horaire (€)</Label>
              <Input
                id="rate"
                type="number"
                value={formData.hourly_rate}
                onChange={(e) => setFormData({ ...formData, hourly_rate: parseFloat(e.target.value) })}
                min={20}
                max={200}
                data-testid="instructor-rate"
              />
            </div>

            <Button type="submit" disabled={submitting} className="submit-btn" data-testid="submit-instructor">
              {submitting ? "Envoi en cours..." : "Soumettre ma demande"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

// Instructor Dashboard with Recurring Lessons
const InstructorDashboard = ({ user }) => {
  const [lessons, setLessons] = useState([]);
  const [instructor, setInstructor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showCreateLesson, setShowCreateLesson] = useState(false);
  const [newLesson, setNewLesson] = useState({
    lesson_type: "private",
    title: "",
    description: "",
    date: format(new Date(), "yyyy-MM-dd"),
    start_time: "09:00",
    end_time: "10:00",
    max_participants: 1,
    price: 50,
    is_recurring: false,
    recurrence_type: "weekly",
    recurrence_end_date: format(addWeeks(new Date(), 4), "yyyy-MM-dd")
  });
  const navigate = useNavigate();

  useEffect(() => {
    if (!user || user.role === "client") {
      navigate("/");
      return;
    }

    const fetchData = async () => {
      try {
        const [meRes, lessonsRes] = await Promise.all([
          axios.get(`${API}/auth/me`, { withCredentials: true }),
          axios.get(`${API}/my-lessons`, { withCredentials: true })
        ]);
        setInstructor(meRes.data.instructor);
        setLessons(lessonsRes.data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [user, navigate]);

  const handleCreateLesson = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API}/lessons`, newLesson, { withCredentials: true });
      
      // Refresh lessons list
      const lessonsRes = await axios.get(`${API}/my-lessons`, { withCredentials: true });
      setLessons(lessonsRes.data);
      
      setShowCreateLesson(false);
      setNewLesson({
        lesson_type: "private",
        title: "",
        description: "",
        date: format(new Date(), "yyyy-MM-dd"),
        start_time: "09:00",
        end_time: "10:00",
        max_participants: 1,
        price: 50,
        is_recurring: false,
        recurrence_type: "weekly",
        recurrence_end_date: format(addWeeks(new Date(), 4), "yyyy-MM-dd")
      });
      
      const count = response.data.lessons_created || 1;
      toast.success(`${count} cours créé(s) !`);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Erreur lors de la création");
    }
  };

  const handleDeleteLesson = async (lessonId) => {
    try {
      await axios.delete(`${API}/lessons/${lessonId}`, { withCredentials: true });
      setLessons(lessons.map(l => l.id === lessonId ? { ...l, status: "cancelled" } : l));
      toast.success("Cours annulé");
    } catch (e) {
      toast.error("Erreur lors de l'annulation");
    }
  };

  if (loading) return <div className="loading-page"><div className="loading-spinner"></div></div>;

  return (
    <div className="page-container" data-testid="instructor-dashboard-page">
      <div className="page-header">
        <h1>Espace moniteur</h1>
        <p>Gérez vos cours et réservations</p>
      </div>

      {instructor?.status === "pending" && (
        <Card className="warning-card">
          <CardContent>
            <p>⏳ Votre profil est en attente de validation par un administrateur.</p>
          </CardContent>
        </Card>
      )}

      {instructor?.status === "rejected" && (
        <Card className="error-card">
          <CardContent>
            <p>❌ Votre demande a été refusée.</p>
          </CardContent>
        </Card>
      )}

      {instructor?.status === "approved" && (
        <>
          <div className="section-header">
            <h2>Mes cours</h2>
            <Dialog open={showCreateLesson} onOpenChange={setShowCreateLesson}>
              <DialogTrigger asChild>
                <Button data-testid="create-lesson-btn">Créer un cours</Button>
              </DialogTrigger>
              <DialogContent className="lesson-dialog">
                <DialogHeader>
                  <DialogTitle>Nouveau cours</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleCreateLesson}>
                  <div className="form-group">
                    <Label>Type de cours</Label>
                    <Select value={newLesson.lesson_type} onValueChange={(v) => setNewLesson({ ...newLesson, lesson_type: v, max_participants: v === "private" ? 1 : newLesson.max_participants })}>
                      <SelectTrigger data-testid="lesson-type-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="private">Particulier</SelectItem>
                        <SelectItem value="group">Collectif</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="form-group">
                    <Label>Titre</Label>
                    <Input value={newLesson.title} onChange={(e) => setNewLesson({ ...newLesson, title: e.target.value })} required data-testid="lesson-title" />
                  </div>
                  <div className="form-group">
                    <Label>Description</Label>
                    <Textarea value={newLesson.description} onChange={(e) => setNewLesson({ ...newLesson, description: e.target.value })} data-testid="lesson-description" />
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <Label>Date</Label>
                      <Input type="date" value={newLesson.date} onChange={(e) => setNewLesson({ ...newLesson, date: e.target.value })} required data-testid="lesson-date" />
                    </div>
                    <div className="form-group">
                      <Label>Début</Label>
                      <Input type="time" value={newLesson.start_time} onChange={(e) => setNewLesson({ ...newLesson, start_time: e.target.value })} required data-testid="lesson-start" />
                    </div>
                    <div className="form-group">
                      <Label>Fin</Label>
                      <Input type="time" value={newLesson.end_time} onChange={(e) => setNewLesson({ ...newLesson, end_time: e.target.value })} required data-testid="lesson-end" />
                    </div>
                  </div>
                  {newLesson.lesson_type === "group" && (
                    <div className="form-group">
                      <Label>Participants max</Label>
                      <Input type="number" value={newLesson.max_participants} onChange={(e) => setNewLesson({ ...newLesson, max_participants: parseInt(e.target.value) })} min={2} max={20} data-testid="lesson-max" />
                    </div>
                  )}
                  <div className="form-group">
                    <Label>Prix (€)</Label>
                    <Input type="number" value={newLesson.price} onChange={(e) => setNewLesson({ ...newLesson, price: parseFloat(e.target.value) })} min={10} data-testid="lesson-price" />
                  </div>
                  
                  {/* Recurring lesson options */}
                  <div className="form-group recurring-section">
                    <div className="checkbox-item">
                      <Checkbox
                        id="is_recurring"
                        checked={newLesson.is_recurring}
                        onCheckedChange={(checked) => setNewLesson({ ...newLesson, is_recurring: checked })}
                        data-testid="lesson-recurring"
                      />
                      <Label htmlFor="is_recurring"><Repeat size={14} /> Cours récurrent</Label>
                    </div>
                    
                    {newLesson.is_recurring && (
                      <div className="recurring-options">
                        <div className="form-group">
                          <Label>Fréquence</Label>
                          <Select value={newLesson.recurrence_type} onValueChange={(v) => setNewLesson({ ...newLesson, recurrence_type: v })}>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="weekly">Hebdomadaire</SelectItem>
                              <SelectItem value="biweekly">Toutes les 2 semaines</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="form-group">
                          <Label>Jusqu'au</Label>
                          <Input type="date" value={newLesson.recurrence_end_date} onChange={(e) => setNewLesson({ ...newLesson, recurrence_end_date: e.target.value })} />
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <DialogFooter>
                    <Button type="submit" data-testid="submit-lesson">Créer</Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          {lessons.length === 0 ? (
            <Card className="empty-state">
              <CardContent>
                <CalendarIcon size={48} />
                <p>Aucun cours créé</p>
              </CardContent>
            </Card>
          ) : (
            <div className="instructor-lessons-list">
              {lessons.map((lesson) => (
                <Card key={lesson.id} className={`lesson-card instructor ${lesson.status}`} data-testid={`my-lesson-${lesson.id}`}>
                  <CardContent>
                    <div className="lesson-info">
                      <h4>
                        {lesson.title}
                        {lesson.is_recurring && <Repeat size={14} className="recurring-icon" />}
                      </h4>
                      <div className="lesson-meta">
                        <span><CalendarIcon size={14} /> {lesson.date}</span>
                        <span><Clock size={14} /> {lesson.start_time} - {lesson.end_time}</span>
                        <span><Users size={14} /> {lesson.current_participants}/{lesson.max_participants}</span>
                        <span><Euro size={14} /> {lesson.price}€</span>
                      </div>
                      <div className="lesson-badges">
                        <Badge variant={lesson.lesson_type === "private" ? "default" : "secondary"}>
                          {lesson.lesson_type === "private" ? "Particulier" : "Collectif"}
                        </Badge>
                        <Badge variant={lesson.status === "available" ? "outline" : lesson.status === "full" ? "default" : "destructive"}>
                          {lesson.status === "available" ? "Disponible" : lesson.status === "full" ? "Complet" : "Annulé"}
                        </Badge>
                      </div>
                    </div>
                    {lesson.bookings?.length > 0 && (
                      <div className="lesson-bookings">
                        <h5>Réservations :</h5>
                        {lesson.bookings.map((booking) => (
                          <div key={booking.id} className="booking-item">
                            <Avatar className="small">
                              <AvatarImage src={booking.user?.picture} />
                              <AvatarFallback>{booking.user?.name?.charAt(0)}</AvatarFallback>
                            </Avatar>
                            <span>{booking.user?.name}</span>
                            <Badge variant={booking.payment_status === "paid" ? "default" : "outline"}>
                              {booking.payment_status === "paid" ? "Payé" : "Non payé"}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    )}
                    {lesson.status === "available" && (
                      <Button variant="outline" onClick={() => handleDeleteLesson(lesson.id)} data-testid={`delete-lesson-${lesson.id}`}>
                        Annuler
                      </Button>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
};

// Admin Dashboard with Commission Stats
const AdminDashboard = ({ user }) => {
  const [stats, setStats] = useState(null);
  const [pendingInstructors, setPendingInstructors] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    if (!user || user.role !== "admin") {
      navigate("/");
      return;
    }

    const fetchData = async () => {
      try {
        const [statsRes, pendingRes] = await Promise.all([
          axios.get(`${API}/admin/stats`, { withCredentials: true }),
          axios.get(`${API}/admin/pending-instructors`, { withCredentials: true })
        ]);
        setStats(statsRes.data);
        setPendingInstructors(pendingRes.data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [user, navigate]);

  const handleApprove = async (instructorId) => {
    try {
      await axios.put(`${API}/instructors/${instructorId}/status`, { status: "approved" }, { withCredentials: true });
      setPendingInstructors(pendingInstructors.filter(i => i.id !== instructorId));
      setStats({ ...stats, total_instructors: stats.total_instructors + 1, pending_instructors: stats.pending_instructors - 1 });
      toast.success("Moniteur approuvé");
    } catch (e) {
      toast.error("Erreur");
    }
  };

  const handleReject = async (instructorId) => {
    try {
      await axios.put(`${API}/instructors/${instructorId}/status`, { status: "rejected" }, { withCredentials: true });
      setPendingInstructors(pendingInstructors.filter(i => i.id !== instructorId));
      setStats({ ...stats, pending_instructors: stats.pending_instructors - 1 });
      toast.success("Moniteur refusé");
    } catch (e) {
      toast.error("Erreur");
    }
  };

  const handleSendReminders = async () => {
    try {
      const response = await axios.post(`${API}/admin/send-reminders`, {}, { withCredentials: true });
      toast.success(response.data.message);
    } catch (e) {
      toast.error("Erreur lors de l'envoi des rappels");
    }
  };

  if (loading) return <div className="loading-page"><div className="loading-spinner"></div></div>;

  return (
    <div className="page-container" data-testid="admin-dashboard-page">
      <div className="page-header">
        <h1>Administration</h1>
        <p>Gérez la plateforme</p>
      </div>

      <div className="stats-grid">
        <Card className="stat-card">
          <CardContent>
            <Users size={24} />
            <div className="stat-value">{stats?.total_users || 0}</div>
            <div className="stat-label">Utilisateurs</div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardContent>
            <Award size={24} />
            <div className="stat-value">{stats?.total_instructors || 0}</div>
            <div className="stat-label">Moniteurs</div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardContent>
            <CalendarIcon size={24} />
            <div className="stat-value">{stats?.total_lessons || 0}</div>
            <div className="stat-label">Cours</div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardContent>
            <Check size={24} />
            <div className="stat-value">{stats?.total_bookings || 0}</div>
            <div className="stat-label">Réservations</div>
          </CardContent>
        </Card>
      </div>

      {/* Revenue Stats */}
      <div className="revenue-section">
        <h2><TrendingUp size={20} /> Revenus</h2>
        <div className="revenue-grid">
          <Card className="revenue-card">
            <CardContent>
              <div className="revenue-label">Chiffre d'affaires total</div>
              <div className="revenue-value">{stats?.total_revenue || 0}€</div>
            </CardContent>
          </Card>
          <Card className="revenue-card commission">
            <CardContent>
              <div className="revenue-label">Commission plateforme ({stats?.commission_rate})</div>
              <div className="revenue-value">{stats?.total_commission || 0}€</div>
            </CardContent>
          </Card>
        </div>
      </div>

      <div className="section-header">
        <h2>Demandes en attente ({stats?.pending_instructors || 0})</h2>
        <Button variant="outline" onClick={handleSendReminders} data-testid="send-reminders-btn">
          Envoyer les rappels 24h
        </Button>
      </div>

      {pendingInstructors.length === 0 ? (
        <Card className="empty-state">
          <CardContent>
            <Check size={48} />
            <p>Aucune demande en attente</p>
          </CardContent>
        </Card>
      ) : (
        <div className="pending-list">
          {pendingInstructors.map((instructor) => (
            <Card key={instructor.id} className="pending-card" data-testid={`pending-${instructor.id}`}>
              <CardContent>
                <div className="pending-info">
                  <Avatar>
                    <AvatarImage src={instructor.user?.picture} />
                    <AvatarFallback>{instructor.user?.name?.charAt(0)}</AvatarFallback>
                  </Avatar>
                  <div>
                    <h4>{instructor.user?.name}</h4>
                    <p>{instructor.user?.email}</p>
                    {instructor.station && (
                      <p className="station"><MapPin size={14} /> {instructor.station.name}</p>
                    )}
                    <p className="bio">{instructor.bio}</p>
                    <div className="instructor-tags">
                      {instructor.specialties?.map((s) => <Badge key={s} variant="secondary">{s}</Badge>)}
                      {instructor.ski_levels?.map((l) => <Badge key={l} variant="outline">{l}</Badge>)}
                    </div>
                    <p className="rate">{instructor.hourly_rate}€/h</p>
                  </div>
                </div>
                <div className="pending-actions">
                  <Button onClick={() => handleApprove(instructor.id)} data-testid={`approve-${instructor.id}`}>
                    <Check size={16} /> Approuver
                  </Button>
                  <Button variant="outline" onClick={() => handleReject(instructor.id)} data-testid={`reject-${instructor.id}`}>
                    <X size={16} /> Refuser
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

// Payment Success
const PaymentSuccess = () => {
  const [status, setStatus] = useState("checking");
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const checkPayment = async () => {
      const params = new URLSearchParams(location.search);
      const sessionId = params.get("session_id");

      if (!sessionId) {
        setStatus("error");
        return;
      }

      let attempts = 0;
      const maxAttempts = 5;

      const poll = async () => {
        try {
          const response = await axios.get(`${API}/payments/status/${sessionId}`, { withCredentials: true });
          if (response.data.payment_status === "paid") {
            setStatus("success");
          } else if (response.data.status === "expired") {
            setStatus("error");
          } else if (attempts < maxAttempts) {
            attempts++;
            setTimeout(poll, 2000);
          } else {
            setStatus("pending");
          }
        } catch (e) {
          setStatus("error");
        }
      };

      poll();
    };

    checkPayment();
  }, [location]);

  return (
    <div className="page-container centered" data-testid="payment-success-page">
      <Card className="payment-status-card">
        <CardContent>
          {status === "checking" && (
            <>
              <div className="loading-spinner"></div>
              <h2>Vérification du paiement...</h2>
            </>
          )}
          {status === "success" && (
            <>
              <div className="success-icon"><Check size={48} /></div>
              <h2>Paiement réussi !</h2>
              <p>Votre réservation est confirmée.</p>
              <Button onClick={() => navigate("/dashboard")}>Voir mes réservations</Button>
            </>
          )}
          {status === "pending" && (
            <>
              <div className="pending-icon"><Clock size={48} /></div>
              <h2>Paiement en cours de traitement</h2>
              <p>Vous recevrez une confirmation par email.</p>
              <Button onClick={() => navigate("/dashboard")}>Retour</Button>
            </>
          )}
          {status === "error" && (
            <>
              <div className="error-icon"><X size={48} /></div>
              <h2>Erreur de paiement</h2>
              <p>Une erreur est survenue. Veuillez réessayer.</p>
              <Button onClick={() => navigate("/dashboard")}>Retour</Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// Main App
function App() {
  const { user, setUser, loading, checkAuth, logout } = useAuth();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  if (loading) {
    return (
      <div className="loading-page">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div className="app">
      <BrowserRouter>
        <Toaster position="top-center" richColors />
        <Header user={user} logout={logout} />
        <main className="main">
          <Routes>
            <Route path="/" element={<Landing user={user} />} />
            <Route path="/auth-callback" element={<AuthCallback setUser={setUser} checkAuth={checkAuth} />} />
            <Route path="/instructors" element={<InstructorsList />} />
            <Route path="/instructor/:id" element={<InstructorDetail user={user} />} />
            <Route path="/lessons" element={<LessonsList user={user} />} />
            <Route path="/dashboard" element={<Dashboard user={user} />} />
            <Route path="/bookings" element={<Dashboard user={user} />} />
            <Route path="/become-instructor" element={<BecomeInstructor user={user} setUser={setUser} />} />
            <Route path="/instructor-dashboard" element={<InstructorDashboard user={user} />} />
            <Route path="/admin" element={<AdminDashboard user={user} />} />
            <Route path="/payment-success" element={<PaymentSuccess />} />
          </Routes>
        </main>
      </BrowserRouter>
    </div>
  );
}

export default App;
