import React, { useState, useEffect } from 'react';
import { AlertDialog, AlertDialogAction, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";

const movieEmojis = [
  { emojis: "🦁👑", movie: "The Lion King" },
  { emojis: "🧙‍♂️💍", movie: "The Lord of the Rings" },
  { emojis: "👻👻👻👻", movie: "Ghostbusters" },
  { emojis: "🦖🏞️", movie: "Jurassic Park" },
  { emojis: "🚢❄️💔", movie: "Titanic" },
  { emojis: "👽☝️🏠", movie: "E.T." },
  { emojis: "🕷️🕸️👨", movie: "Spider-Man" },
  { emojis: "🧙‍♂️⚡👓", movie: "Harry Potter" },
  { emojis: "🤖❤️🌱", movie: "WALL-E" },
  { emojis: "🐀👨‍🍳", movie: "Ratatouille" }
];

const MovieEmojiGame = ({ isVisible, onClose }) => {
  const [currentMovie, setCurrentMovie] = useState(null);
  const [userGuess, setUserGuess] = useState('');
  const [message, setMessage] = useState('');
  const [score, setScore] = useState(0);

  useEffect(() => {
    if (isVisible) {
      newGame();
    }
  }, [isVisible]);

  const newGame = () => {
    const randomMovie = movieEmojis[Math.floor(Math.random() * movieEmojis.length)];
    setCurrentMovie(randomMovie);
    setUserGuess('');
    setMessage('');
  };

  const handleGuess = () => {
    if (userGuess.toLowerCase() === currentMovie.movie.toLowerCase()) {
      setMessage('Correct! Well done!');
      setScore(score + 1);
      setTimeout(newGame, 1500);
    } else {
      setMessage('Sorry, that\'s not correct. Try again!');
    }
  };

  if (!isVisible) return null;

  return (
    <AlertDialog open={isVisible} onOpenChange={onClose}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Guess the Movie!</AlertDialogTitle>
          <AlertDialogDescription>
            While we process your video, try to guess the movie from the emojis. Your score: {score}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <div className="text-center my-4">
          <p className="text-4xl mb-4">{currentMovie?.emojis}</p>
          <input
            type="text"
            value={userGuess}
            onChange={(e) => setUserGuess(e.target.value)}
            placeholder="Enter your guess"
            className="border p-2 rounded w-full mb-2"
          />
          <Button onClick={handleGuess}>Submit Guess</Button>
          {message && <p className="mt-2">{message}</p>}
        </div>
        <AlertDialogFooter>
          <AlertDialogAction onClick={onClose}>Close Game</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};

export default MovieEmojiGame;