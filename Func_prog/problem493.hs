import Text.Printf (printf)

main :: IO ()
main = putStrLn answer

choose :: Integer -> Integer -> Integer
choose n r = product [n - r + 1..n] `div` product [1..r]

expectedValue :: Double
expectedValue = 7 * (1 - fromIntegral (choose 60 20) / fromIntegral (choose 70 20))

answer :: String
answer = printf "%.9f" expectedValue
