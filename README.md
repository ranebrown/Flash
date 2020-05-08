# Flash

Flash cards for the terminal. Original idea came from
[Fla.sh](https://github.com/tallguyjenks/fla.sh). This version is written in
python rather than bash and has a few improvements:

1. Uses `yaml` files instead of `csv` which makes editing and formatting questions
   easier (line breaks, special characters, lists, etc.).

   With `yaml` you can do something like this:

   ```yaml
   - subject: Stuff to know
     question: |
       How do you add two numbers?
     answer: |
       1. First, take number a
       2. Second, take number b
       3. Add them together into c

       a + b + c

       OR

       2 + 2 = 4
     priority: 1
   ```

   But in `csv` the question would look like:

   ```csv
   Stuff to know:How do you add two numbers?:1. First take number a 2. Second take number b 3. Add them together into c a + b + c OR 2 + 2 = 4:1
   ```

2. Uses command line arguments to select a deck instead of requiring
   non-standard tools like `fzf` and `bat` (which are both awesome).
3. Better card selection algorithm and options:
    - Cycle through all cards starting with the highest priority
    - `-x` flag to exclude lowest priority cards so you can work through a deck
      and stop showing cards you have memorized
    - Show only cards of a specific priority
